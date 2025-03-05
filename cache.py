import boto3
import concurrent.futures
from datetime import datetime, timedelta

# Initialize clients for EC2 and CloudTrail
ec2 = boto3.client('ec2')
cloudtrail = boto3.client('cloudtrail')

# Fetch available volumes in parallel
def fetch_available_volumes():
    paginator = ec2.get_paginator('describe_volumes')
    page_iterator = paginator.paginate(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ],
        PaginationConfig={'PageSize': 100}
    )

    volumes = []
    for page in page_iterator:
        for volume in page['Volumes']:
            volumes.append(volume)
    return volumes

# Fetch detach time for a volume using CloudTrail
def get_last_detach_time(volume_id):
    try:
        paginator = cloudtrail.get_paginator('lookup_events')
        page_iterator = paginator.paginate(
            LookupAttributes=[
                {'AttributeKey': 'EventName', 'AttributeValue': 'DetachVolume'}
            ],
            StartTime=datetime.now() - timedelta(days=90),
            EndTime=datetime.now()
        )

        for page in page_iterator:
            for event in page['Events']:
                for resource in event['Resources']:
                    if resource['ResourceType'] == 'AWS::EC2::Volume' and resource['ResourceName'] == volume_id:
                        return event['EventTime']
        return None
    except Exception as e:
        print(f"Error fetching detach time for volume {volume_id}: {str(e)}")
        return None

# Organize volumes by VSAD
def organize_volumes_by_vsad(volumes):
    vsad_data = {}
    for volume in volumes:
        vsad = "Unknown"
        if 'Tags' in volume:
            for tag in volume['Tags']:
                if tag['Key'] == 'VSAD':
                    vsad = tag['Value']
                    break

        if vsad not in vsad_data:
            vsad_data[vsad] = []
        vsad_data[vsad].append(volume)

    return vsad_data

# Main logic to process volumes and fetch detach times in parallel
def process_volumes():
    volumes = fetch_available_volumes()
    print(f"Total available volumes: {len(volumes)}")

    # Organize volumes by VSAD
    vsad_data = organize_volumes_by_vsad(volumes)

    # Fetch detach times in parallel
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_volume = {executor.submit(get_last_detach_time, vol['VolumeId']): vol for vol in volumes}

        for future in concurrent.futures.as_completed(future_to_volume):
            volume = future_to_volume[future]
            try:
                last_detach_time = future.result()
                if last_detach_time:
                    volume['LastDetached'] = last_detach_time
                    vsad = next((tag['Value'] for tag in volume.get('Tags', []) if tag['Key'] == 'VSAD'), 'Unknown')
                    if vsad not in results:
                        results[vsad] = []
                    results[vsad].append(volume)
            except Exception as e:
                print(f"Error processing volume {volume['VolumeId']}: {str(e)}")

    # Display results
    for vsad, volumes in results.items():
        print(f"\nVSAD: {vsad}")
        for vol in volumes:
            print(f"  Volume ID: {vol['VolumeId']}, Last Detached: {vol['LastDetached']}")

# Run the script
process_volumes()





import boto3
import time
import random
from datetime import datetime, timedelta

# Initialize clients for EC2 and CloudTrail
ec2 = boto3.client('ec2')
cloudtrail = boto3.client('cloudtrail')

# Retry decorator with exponential backoff and jitter
def retry_with_backoff(func):
    def wrapper(*args, **kwargs):
        max_retries = 5  # Maximum number of retries
        base_delay = 1  # Initial delay in seconds

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # If the max retries are reached, raise the exception
                if attempt == max_retries - 1:
                    print(f"Max retries reached for {func.__name__}: {str(e)}")
                    raise
                else:
                    # Calculate delay with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Retrying {func.__name__} in {delay:.2f} seconds (attempt {attempt + 1})...")
                    time.sleep(delay)
    return wrapper

# Function to get available volumes with their last detach time and organize by VSAD
@retry_with_backoff
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
@retry_with_backoff
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
import logging
import time
import random
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

def get_elasticache_clusters(region, cluster_env):
    session = boto3.Session()
    aws_boto_config = get_boto3_config(cluster_env, region)
    elasticache_client = session.client('elasticache', config=aws_boto_config, region_name=region)
    
    # Exponential backoff settings
    max_attempts = 5  # Maximum number of retry attempts
    base_wait = 1  # Base wait time in seconds

    try:
        clusters = []
        paginator = elasticache_client.get_paginator('describe_cache_clusters')

        # Retry mechanism with exponential backoff for getting clusters
        for attempt in range(1, max_attempts + 1):
            try:
                for page in paginator.paginate():
                    clusters.extend(page['CacheClusters'])
                break  # Exit the retry loop if successful
            except ClientError as ex:
                error_code = ex.response['Error']['Code']
                if error_code == 'ThrottlingException' or error_code == 'RequestLimitExceeded':
                    # Calculate wait time with exponential backoff and jitter
                    wait_time = base_wait * (2 ** attempt) + random.uniform(0, 1)
                    logging.warning(f"Throttling exception detected. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise ex

        # Build detailed cluster data including VSAD level data
        vsad_data = []
        for cluster in clusters:
            cluster_id = cluster['CacheClusterId']
            cluster_arn = cluster['ARN']
            engine = cluster['Engine']
            num_of_cache_nodes = cluster['NumCacheNodes']
            cache_node_type = cluster['CacheNodeType']

            # Retry getting tags with exponential backoff
            tags_dict = {}
            for attempt in range(1, max_attempts + 1):
                try:
                    tags_response = elasticache_client.list_tags_for_resource(ResourceName=cluster_arn)
                    tags = tags_response.get('TagList', [])
                    tags_dict = {tag['Key']: tag['Value'] for tag in tags}
                    break  # Exit the retry loop if successful
                except ClientError as ex:
                    error_code = ex.response['Error']['Code']
                    if error_code == 'ThrottlingException' or error_code == 'RequestLimitExceeded':
                        wait_time = base_wait * (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"Throttling exception detected while getting tags. Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise ex

            # Get VSAD value from tags
            vsad = tags_dict.get('VSAD', 'Unknown')

            # Append the cluster details to VSAD data list
            vsad_data.append({
                'VSAD': vsad,
                'Engine': engine,
                'ClusterARN': cluster_arn,
                'ClusterName': cluster_id,
                'NumOfCacheNodes': num_of_cache_nodes,
                'CacheNodeType': cache_node_type,
                'Tags': tags_dict  # Include full tags dictionary if needed
            })

        return vsad_data
    
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as ex:
        logging.error(f'Failed to get_elasticache_clusters: {ex}')
        raise ex






import boto3
from fastapi import HTTPException

def get_elasticache_clusters():
    elasticache_client = boto3.client('elasticache')
    clusters = []
    
    paginator = elasticache_client.get_paginator('describe_cache_clusters')
    for page in paginator.paginate():
        clusters.extend(page['CacheClusters'])

    detailed_clusters = []
    
    for cluster in clusters:
        cluster_id = cluster['CacheClusterId']
        
        # Get tags for the cluster
        arn = f"arn:aws:elasticache:{cluster['PreferredAvailabilityZone'].split(':')[0]}:{cluster['CacheClusterId']}"
        tags_response = elasticache_client.list_tags_for_resource(ResourceName=arn)
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}
        
        # Append detailed cluster info
        detailed_clusters.append({
            'CacheClusterId': cluster_id,
            'Tags': tags
        })
    
    return detailed_clusters

def group_elasticache_clusters_by_vsad():
    try:
        clusters = get_elasticache_clusters()
        vsad_counts = {}

        for cluster in clusters:
            tags = cluster.get('Tags', {})
            vsad = tags.get('Vsad', None)
            if vsad:
                if vsad not in vsad_counts:
                    vsad_counts[vsad] = 0
                vsad_counts[vsad] += 1

        return vsad_counts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












import boto3
import logging
import time
import random
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

def get_elasticache_clusters(region, cluster_env):
    session = boto3.Session()
    aws_boto_config = get_boto3_config(cluster_env, region)
    elasticache_client = session.client('elasticache', config=aws_boto_config, region_name=region)
    
    # Exponential backoff settings
    max_attempts = 5  # Maximum number of retry attempts
    base_wait = 1  # Base wait time in seconds
    
    try:
        clusters = []
        paginator = elasticache_client.get_paginator('describe_cache_clusters')

        # Retry mechanism with exponential backoff
        for attempt in range(1, max_attempts + 1):
            try:
                for page in paginator.paginate():
                    clusters.extend(page['CacheClusters'])
                break  # Exit the retry loop if successful
            except ClientError as ex:
                error_code = ex.response['Error']['Code']
                if error_code == 'ThrottlingException' or error_code == 'RequestLimitExceeded':
                    # Calculate wait time with exponential backoff and jitter
                    wait_time = base_wait * (2 ** attempt) + random.uniform(0, 1)
                    logging.warning(f"Throttling exception detected. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise ex
        
        detailed_clusters = []
        for cluster in clusters:
            cluster_id = cluster['CacheClusterId']
            cluster_arn = cluster['ARN']
            
            # Retry getting tags with exponential backoff
            for attempt in range(1, max_attempts + 1):
                try:
                    tags_response = elasticache_client.list_tags_for_resource(ResourceName=cluster_arn)
                    tags = tags_response.get('TagList', [])
                    tags_dict = {tag['Key']: tag['Value'] for tag in tags}
                    break  # Exit the retry loop if successful
                except ClientError as ex:
                    error_code = ex.response['Error']['Code']
                    if error_code == 'ThrottlingException' or error_code == 'RequestLimitExceeded':
                        wait_time = base_wait * (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"Throttling exception detected while getting tags. Retrying in {wait_time:.2f} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise ex
            
            # Append detailed cluster info
            detailed_clusters.append({
                'CacheClusterId': cluster_id,
                'Tags': tags_dict
            })
        
        return detailed_clusters
    
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as ex:
        logging.error(f'Failed to get_elasticache_clusters: {ex}')
        raise ex






import requests
import os
import json
from datetime import datetime, timedelta
import pytz

# Set your New Relic API key
NEW_RELIC_API_KEY = os.getenv("NEW_RELIC_API_KEY")

# List of services to monitor
SERVICES = ["service-a", "service-b", "service-c"]

# Define EST timezone
EST = pytz.timezone("US/Eastern")

def get_tpm_for_service(service, region):
    """Fetch TPM from New Relic for a given service in the last 3 days (9 AM - 8 PM EST)."""
    url = "https://api.newrelic.com/v2/query"
    headers = {"Api-Key": NEW_RELIC_API_KEY, "Content-Type": "application/json"}
    
    total_tpm = []

    for days_ago in range(1, 4):  # Last 3 days
        start_time = datetime.now(EST) - timedelta(days=days_ago)
        start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time.replace(hour=20, minute=0, second=0, microsecond=0)

        # Convert to UTC for NRQL query
        start_utc = start_time.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
        end_utc = end_time.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

        # NRQL query to fetch TPM
        query = f"""
        SELECT count(*) FROM Transaction 
        WHERE appName='{service}' AND region='{region}'
        SINCE '{start_utc}' UNTIL '{end_utc}' 
        FACET hourOf(timestamp) TIMESERIES 1 minute
        """

        response = requests.post(url, headers=headers, json={"nrql": query})
        data = response.json()

        if "results" in data:
            tpm_values = [entry["count"] for entry in data["facets"]]
            if tpm_values:
                avg_tpm = sum(tpm_values) // len(tpm_values)
                total_tpm.append(avg_tpm)

    return sum(total_tpm) // len(total_tpm) if total_tpm else 0

def get_tpm_for_all_services(cluster_name, region, cluster_env):
    """Fetch and return average TPM for all services."""
    
    result = {
        "cluster_name": cluster_name,
        "region": region,
        "cluster_env": cluster_env,
        "services": {}
    }
    
    for service in SERVICES:
        avg_tpm = get_tpm_for_service(service, region)
        result["services"][service] = {"avg_tpm": avg_tpm}

    return result

# Example usage
if __name__ == "__main__":
    cluster_name = "eks-cluster-1"
    region = "us-east-1"
    cluster_env = "prod"
    
    tpm_data = get_tpm_for_all_services(cluster_name, region, cluster_env)
    
    print(json.dumps(tpm_data, indent=4))
