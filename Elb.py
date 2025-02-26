import requests
import time
import base64

# API Credentials
username_password = "your_username:your_password"
encoded_auth = base64.b64encode(username_password.encode()).decode()

# Headers
headers = {
    "accept": "application/json",
    "Auth": f"Basic {encoded_auth}",
    "Content-Type": "application/json"
}

# API Endpoint for Encryption Request
url_put = "https://ansibleplus.verizon.com/aws/ec2/wls-np/images/encrypt?vsad=IZIV"
data = {
    "amiLabel": "Red Hat Enterprise Linux 8 (Latest)",
    "amiTags": "Key1=Value1\nKey2=Value2",
    "UserId": "string"
}

# Step 1: Send PUT Request to Encrypt Image
response = requests.put(url_put, json=data, headers=headers)
if response.status_code != 200:
    print(f"Error: {response.text}")
    exit()

audit_id = response.json().get("AuditID")
print(f"Audit ID: {audit_id}")

# Step 2: Poll the GET API Every 2 Minutes Until Completed
url_get = f"https://ansibleplus.verizon.com/app/play/{audit_id}/results?vsad=IZIV&withLogs=false"

while True:
    get_response = requests.get(url_get, headers=headers)
    if get_response.status_code != 200:
        print(f"Error: {get_response.text}")
        exit()
    
    result = get_response.json()
    
    if result.get("status") == "COMPLETED":
        break
    
    print("Waiting for completion...")
    time.sleep(120)  # Wait for 2 minutes

# Step 3: Extract and Print NONPROD AMIs
nonprod = result.get("outputs", {}).get("NONPROD", {})
us_east_1_ami = nonprod.get("us-east-1")
us_west_2_ami = nonprod.get("us-west-2")

print(f"NONPROD us-east-1 AMI: {us_east_1_ami}")
print(f"NONPROD us-west-2 AMI: {us_west_2_ami}")









import boto3
from datetime import datetime, timedelta

# Initialize clients for EC2 and CloudTrail
ec2 = boto3.client('ec2')
cloudtrail = boto3.client('cloudtrail')

# Function to get available volumes with their last detach time and organize by VSAD
def get_volumes_vsad_wise():
    try:
        # Initialize paginator for describe_volumes
        paginator = ec2.get_paginator('describe_volumes')
        
        # Create a pagination iterator with the required filters
        page_iterator = paginator.paginate(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
        
        # Dictionary to store VSAD-wise volume data
        vsad_data = {}

        # Iterate over each page of volumes
        for page in page_iterator:
            # Iterate over each volume in the current page
            for volume in page['Volumes']:
                volume_id = volume['VolumeId']
                vsad = "Unknown"

                # Retrieve the VSAD tag, if present
                if 'Tags' in volume:
                    for tag in volume['Tags']:
                        if tag['Key'] == 'VSAD':
                            vsad = tag['Value']
                            break

                # Fetch the last detach time using CloudTrail
                last_detach_time = get_last_detach_time(volume_id)

                # If no detach time is found, skip the volume
                if not last_detach_time:
                    continue

                # Organize data by VSAD
                if vsad not in vsad_data:
                    vsad_data[vsad] = []

                # Append the volume details to the VSAD entry
                vsad_data[vsad].append({
                    'VolumeId': volume_id,
                    'LastDetached': last_detach_time
                })

        # Print the VSAD-wise organized volume data
        for vsad, volumes in vsad_data.items():
            print(f"\nVSAD: {vsad}")
            for vol in volumes:
                print(f"  Volume ID: {vol['VolumeId']}, Last Detached: {vol['LastDetached']}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

# Function to get the last detach time for a volume using CloudTrail
def get_last_detach_time(volume_id):
    try:
        # Initialize CloudTrail paginator to search for DetachVolume events
        paginator = cloudtrail.get_paginator('lookup_events')
        
        # Set a filter to search for DetachVolume events for the given volume
        page_iterator = paginator.paginate(
            LookupAttributes=[
                {
                    'AttributeKey': 'EventName',
                    'AttributeValue': 'DetachVolume'
                }
            ],
            StartTime=datetime.now() - timedelta(days=90),  # Search last 90 days
            EndTime=datetime.now()
        )

        # Iterate over each page of CloudTrail events
        for page in page_iterator:
            for event in page['Events']:
                # Check if the volume ID matches in the event resources
                for resource in event['Resources']:
                    if resource['ResourceType'] == 'AWS::EC2::Volume' and resource['ResourceName'] == volume_id:
                        # Return the event time when the volume was detached
                        return event['EventTime']
                        
        # If no event is found, return None
        return None

    except Exception as e:
        print(f"Error fetching detach time for volume {volume_id}: {str(e)}")
        return None

# Run the function
get_volumes_vsad_wise()












import boto3
from datetime import datetime

# Initialize EC2 client
ec2 = boto3.client('ec2')

# Function to get available volumes and their last detached date using paginator and organize by VSAD
def get_volumes_vsad_wise():
    try:
        # Initialize paginator for describe_volumes
        paginator = ec2.get_paginator('describe_volumes')
        
        # Create a pagination iterator with the required filters
        page_iterator = paginator.paginate(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
        
        # Dictionary to store VSAD-wise volume data
        vsad_data = {}

        # Iterate over each page of volumes
        for page in page_iterator:
            # Iterate over each volume in the current page
            for volume in page['Volumes']:
                volume_id = volume['VolumeId']
                last_detached_time = None
                vsad = "Unknown"

                # Retrieve the VSAD tag, if present
                if 'Tags' in volume:
                    for tag in volume['Tags']:
                        if tag['Key'] == 'VSAD':
                            vsad = tag['Value']
                            break

                # Check the volume's attachment history
                if 'Attachments' in volume:
                    for attachment in volume['Attachments']:
                        # Check if the volume was detached
                        if attachment['State'] == 'detached':
                            detach_time = attachment['DetachTime']
                            # Update the last_detached_time to the most recent detach time
                            if last_detached_time is None or detach_time > last_detached_time:
                                last_detached_time = detach_time
                
                # Organize data by VSAD
                if vsad not in vsad_data:
                    vsad_data[vsad] = []

                # Append the volume details to the VSAD entry
                vsad_data[vsad].append({
                    'VolumeId': volume_id,
                    'LastDetached': last_detached_time if last_detached_time else "No detach record found"
                })

        # Print the VSAD-wise organized volume data
        for vsad, volumes in vsad_data.items():
            print(f"\nVSAD: {vsad}")
            for vol in volumes:
                print(f"  Volume ID: {vol['VolumeId']}, Last Detached: {vol['LastDetached']}")
                
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function
get_volumes_vsad_wise()






import boto3
from datetime import datetime

# Initialize EC2 client
ec2 = boto3.client('ec2')

# Function to get available volumes and their last detached date using paginator
def get_available_volumes_with_last_detached():
    try:
        # Initialize paginator for describe_volumes
        paginator = ec2.get_paginator('describe_volumes')
        
        # Create a pagination iterator with the required filters
        page_iterator = paginator.paginate(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
        
        # Iterate over each page of volumes
        for page in page_iterator:
            # Iterate over each volume in the current page
            for volume in page['Volumes']:
                volume_id = volume['VolumeId']
                last_detached_time = None

                # Check the volume's attachment history
                if 'Attachments' in volume:
                    for attachment in volume['Attachments']:
                        # Check if the volume was detached
                        if attachment['State'] == 'detached':
                            detach_time = attachment['DetachTime']
                            # Update the last_detached_time to the most recent detach time
                            if last_detached_time is None or detach_time > last_detached_time:
                                last_detached_time = detach_time
                
                # Print volume ID and last detached time if available
                if last_detached_time:
                    print(f"Volume ID: {volume_id}, Last Detached: {last_detached_time}")
                else:
                    print(f"Volume ID: {volume_id}, No detach record found.")
                
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function
get_available_volumes_with_last_detached()









import boto3
from datetime import datetime

# Initialize EC2 client
ec2 = boto3.client('ec2')

# Function to get available volumes and their last detached date
def get_available_volumes_with_last_detached():
    try:
        # Describe all volumes with "available" state
        response = ec2.describe_volumes(
            Filters=[
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ]
        )
        
        # Iterate over each available volume
        for volume in response['Volumes']:
            volume_id = volume['VolumeId']
            last_detached_time = None
            
            # Get the volume's attachment history
            if 'Attachments' in volume:
                for attachment in volume['Attachments']:
                    # Check if the volume was attached and detached
                    if attachment['State'] == 'detached':
                        detach_time = attachment['DetachTime']
                        # Update the last_detached_time to the most recent detach time
                        if last_detached_time is None or detach_time > last_detached_time:
                            last_detached_time = detach_time
            
            # Print volume ID and last detached time if available
            if last_detached_time:
                print(f"Volume ID: {volume_id}, Last Detached: {last_detached_time}")
            else:
                print(f"Volume ID: {volume_id}, No detach record found.")
                
    except Exception as e:
        print(f"Error: {str(e)}")

# Run the function
get_available_volumes_with_last_detached()









import boto3

# Initialize the EC2 client
ec2_client = boto3.client('ec2')

# Function to fetch instances and associated volumes that don't have DeleteOnTermination set to True
def fetch_ec2_with_volumes_without_delete_on_termination():
    try:
        # Describe all running instances
        instances = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )['Reservations']

        # Initialize a dictionary to store results by VSAD tag
        vsad_results = {}

        # Iterate over each instance and check its block device mappings
        for reservation in instances:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                block_device_mappings = instance.get('BlockDeviceMappings', [])
                tags = instance.get('Tags', [])

                # Get the VSAD tag
                vsad_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'VSAD'), None)

                if not vsad_tag:
                    # Skip instance if VSAD tag is not found
                    continue

                # Iterate over attached volumes, exclude root volumes, and check DeleteOnTermination flag
                for block_device in block_device_mappings:
                    volume_id = block_device['Ebs']['VolumeId']
                    delete_on_termination = block_device['Ebs'].get('DeleteOnTermination', False)
                    device_name = block_device['DeviceName']

                    # Exclude root volumes (typically device names like /dev/sda1 or /dev/xvda)
                    if device_name == instance['RootDeviceName']:
                        continue

                    # If DeleteOnTermination is not set to True, add to the result
                    if not delete_on_termination:
                        # Initialize the VSAD key in the result dictionary if not already present
                        if vsad_tag not in vsad_results:
                            vsad_results[vsad_tag] = []

                        # Append the instance and volume information to the corresponding VSAD entry
                        vsad_results[vsad_tag].append({
                            'InstanceId': instance_id,
                            'VolumeId': volume_id,
                            'DeviceName': device_name
                        })

        return vsad_results


    

    except Exception as e:
        print(f"Error fetching instances: {str(e)}")
        return {}

# Fetch and print the EC2 instances with volumes that don't have DeleteOnTermination set to True
vsad_volumes = fetch_ec2_with_volumes_without_delete_on_termination()











# Print the results
for vsad, instances in vsad_volumes.items():
    print(f"VSAD: {vsad}")
    for instance in instances:
        print(f"  InstanceId: {instance['InstanceId']}, VolumeId: {instance['VolumeId']}, Device: {instance['DeviceName']}")
