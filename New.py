import pandas as pd
import json

# Load JSON data from a file
with open('data.json') as json_file:
    json_data = json.load(json_file)

# Convert JSON to a DataFrame
# Handling nested JSON if the structure is like in the image
data = []
for key, value in json_data.items():
    for item in value:
        item['Category'] = key  # Add a category column if needed (e.g., "BGPV" or "GOUV")
        data.append(item)

df = pd.DataFrame(data)

# Save DataFrame to CSV
df.to_csv('output.csv', index=False)

print("JSON data has been successfully converted to CSV.")




import pandas as pd
import json

# Load JSON data from a file
with open('data.json') as json_file:
    json_data = json.load(json_file)

# Convert JSON to a DataFrame
df = pd.json_normalize(json_data)

# Save DataFrame to Excel
df.to_excel('output.xlsx', index=False, engine='openpyxl')

print("JSON data has been successfully converted to Excel.")




import boto3
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to implement exponential backoff with jitter
def backoff_with_jitter(attempt, base_delay=1, max_delay=60):
    delay = min(base_delay * (2 ** attempt), max_delay)
    delay_with_jitter = delay / 2 + random.uniform(0, delay / 2)
    time.sleep(delay_with_jitter)

# Function to get all available EBS volumes, accepting region and env as parameters
def get_available_volumes(region, env):
    # Initialize the EC2 client with the specified region
    ec2_client = boto3.client('ec2', region_name=region)
    
    paginator = ec2_client.get_paginator('describe_volumes')
    response_iterator = paginator.paginate(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )
    available_volumes = []
    for page in response_iterator:
        for volume in page['Volumes']:
            available_volumes.append(volume['VolumeId'])
    return available_volumes

# Function to get the detach time for a volume from CloudTrail, accepting region and env
def get_detach_time(volume_id, region, env, max_retries=5):
    # Initialize the CloudTrail client with the specified region
    cloudtrail_client = boto3.client('cloudtrail', region_name=region)

    attempt = 0
    while attempt < max_retries:
        try:
            response = cloudtrail_client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'ResourceName',
                        'AttributeValue': volume_id
                    }
                ],
                MaxResults=10
            )
            
            for event in response['Events']:
                if 'DetachVolume' in event['EventName']:
                    return event['EventTime']
            return None
        except Exception as e:
            print(f"Error fetching detach time for {volume_id}: {str(e)}")
            if 'Throttling' in str(e) or 'Rate exceeded' in str(e):
                attempt += 1
                print(f"Throttling detected. Attempt {attempt} with backoff...")
                backoff_with_jitter(attempt)
            else:
                break
    return None

# Function to collect detach times, accepting region and env as parameters
def collect_detach_times(region, env):
    available_volumes = get_available_volumes(region, env)
    print(f"Found {len(available_volumes)} available volumes.")

    detach_times = {}
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(get_detach_time, volume_id, region, env): volume_id for volume_id in available_volumes}
        
        for future in as_completed(futures):
            volume_id = futures[future]
            detach_time = future.result()
            if detach_time:
                detach_times[volume_id] = detach_time

    return detach_times









import boto3
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Boto3 clients
ec2_client = boto3.client('ec2')
cloudtrail_client = boto3.client('cloudtrail')

# Function to implement exponential backoff with jitter
def backoff_with_jitter(attempt, base_delay=1, max_delay=60):
    # Exponential backoff with jitter formula
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Adding jitter
    delay_with_jitter = delay / 2 + random.uniform(0, delay / 2)
    time.sleep(delay_with_jitter)

# Function to get all available EBS volumes
def get_available_volumes():
    paginator = ec2_client.get_paginator('describe_volumes')
    response_iterator = paginator.paginate(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )
    available_volumes = []
    for page in response_iterator:
        for volume in page['Volumes']:
            available_volumes.append(volume['VolumeId'])
    return available_volumes

# Function to get the detach time for a volume from CloudTrail with retry logic
def get_detach_time(volume_id, max_retries=5):
    attempt = 0
    while attempt < max_retries:
        try:
            # Filter CloudTrail events for the specific volume and detach action
            response = cloudtrail_client.lookup_events(
                LookupAttributes=[
                    {
                        'AttributeKey': 'ResourceName',
                        'AttributeValue': volume_id
                    }
                ],
                MaxResults=10
            )
            
            # Iterate through events to find the 'DetachVolume' event
            for event in response['Events']:
                if 'DetachVolume' in event['EventName']:
                    return event['EventTime']
            return None
        except Exception as e:
            print(f"Error fetching detach time for {volume_id}: {str(e)}")
            
            # Check if error is related to throttling
            if 'Throttling' in str(e) or 'Rate exceeded' in str(e):
                attempt += 1
                print(f"Throttling detected. Attempt {attempt} with backoff...")
                backoff_with_jitter(attempt)
            else:
                break  # For non-throttling errors, break the loop and do not retry
    return None

# Main function to collect detach times
def collect_detach_times():
    available_volumes = get_available_volumes()
    print(f"Found {len(available_volumes)} available volumes.")

    # Use ThreadPoolExecutor to parallelize the CloudTrail lookup
    detach_times = {}
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(get_detach_time, volume_id): volume_id for volume_id in available_volumes}
        
        for future in as_completed(futures):
            volume_id = futures[future]
            detach_time = future.result()
            if detach_time:
                detach_times[volume_id] = detach_time

    return detach_times

if __name__ == '__main__':
    detach_info = collect_detach_times()
    print(f"Detach times for available volumes: {detach_info}")









import boto3

def get_alb_tags_by_vsad():
    # Create a Boto3 client for ELBv2 (ALBs)
    client = boto3.client('elbv2')

    # Step 1: Retrieve all ALBs
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    # Step 2: Iterate over each ALB to retrieve its tags
    for lb in load_balancers:
        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']

        # Step 3: Get the tags for the ALB using its ARN
        tags_response = client.describe_tags(
            ResourceArns=[lb_arn]
        )
        
        # Step 4: Extract tags into a dictionary
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        
        # Step 5: Get the VSAD tag value if it exists
        vsad = tags.get('VSAD')

        # If VSAD tag is found, group the ALB data under the corresponding VSAD key
        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []

            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })
    
    return vsad_data

# Example usage
if __name__ == '__main__':
    vsad_data = get_alb_tags_by_vsad()
    
    for vsad, albs in vsad_data.items():
        print(f"VSAD: {vsad}")
        for alb in albs:
            print(f"  ALB Name: {alb['LoadBalancerName']}")
            print(f"  ALB ARN: {alb['LoadBalancerArn']}")
            print(f"  Tags: {alb['Tags']}")
        print("\n")





import boto3

def get_alb_tags_by_vsad():
    client = boto3.client('elbv2')
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    for lb in load_balancers:
        if lb['Type'] != 'application':  # Filter only ALBs
            continue

        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']
        tags_response = client.describe_tags(ResourceArns=[lb_arn])
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        vsad = tags.get('VSAD')

        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []
            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })

    return vsad_data


def get_nlb_tags_by_vsad():
    client = boto3.client('elbv2')
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    for lb in load_balancers:
        if lb['Type'] != 'network':  # Filter only NLBs
            continue

        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']
        tags_response = client.describe_tags(ResourceArns=[lb_arn])
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        vsad = tags.get('VSAD')

        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []
            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })

    return vsad_data
