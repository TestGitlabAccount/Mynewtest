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
