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
