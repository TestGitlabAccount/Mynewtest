from fastapi import FastAPI, HTTPException
import boto3
import asyncio
import logging
from threading import Semaphore

# Constants
CONCURRENT_TAGS = 5  # Max concurrent tag fetches to avoid throttling
MAX_RETRIES = 5  # Maximum retries for exponential backoff
semaphore = Semaphore(CONCURRENT_TAGS)  # Semaphore to limit concurrency

# Logging setup
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# Async function to fetch tags for a cluster
async def fetch_cluster_tags_async(cluster_arn, elasticache_client):
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                response = await asyncio.to_thread(
                    elasticache_client.list_tags_for_resource, ResourceName=cluster_arn
                )
                tags = response.get("TagList", [])
                return {tag["Key"]: tag["Value"] for tag in tags}
            except Exception as e:
                if "Throttling" in str(e) or "Rate exceeded" in str(e):
                    sleep_time = (2 ** attempt) + (time.time() % 1)
                    logging.warning(f"Throttling error. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1})")
                    await asyncio.sleep(sleep_time)
                else:
                    logging.error(f"Error fetching tags for {cluster_arn}: {e}")
                    break
        raise Exception(f"Max retries exceeded for {cluster_arn}")

# Async function to fetch detailed cluster information
async def fetch_cluster_details_async(cluster, elasticache_client):
    try:
        cluster_id = cluster.get("CacheClusterId")
        cluster_arn = cluster.get("ARN")
        if not cluster_id or not cluster_arn:
            logging.warning(f"Skipping cluster with missing data: {cluster}")
            return None

        # Fetch cluster tags asynchronously
        tags = await fetch_cluster_tags_async(cluster_arn, elasticache_client)

        # Prepare cluster details
        creation_time = cluster.get("CacheClusterCreateTime")
        return {
            "ClusterName": cluster_id,
            "ClusterARN": cluster_arn,
            "Engine": cluster.get("Engine"),
            "NumOfCacheNodes": cluster.get("NumCacheNodes"),
            "CacheNodeType": cluster.get("CacheNodeType"),
            "CreationTime": creation_time.isoformat() if creation_time else None,
            "Tags": tags,
            "VSAD": tags.get("VSAD", "Unknown"),
        }
    except Exception as e:
        logging.error(f"Error fetching details for cluster {cluster.get('CacheClusterId', 'Unknown')}: {e}")
        return None

# Async function to fetch all ElastiCache clusters
async def get_elasticache_clusters_async(region):
    """
    Fetches details of all ElastiCache clusters in the specified region using asyncio.
    """
    session = boto3.Session()
    aws_boto_config = boto3.session.Config(retries={"max_attempts": 10, "mode": "standard"})
    elasticache_client = session.client("elasticache", config=aws_boto_config, region_name=region)

    try:
        # Fetch cluster list
        clusters = []
        paginator = elasticache_client.get_paginator("describe_cache_clusters")
        for page in paginator.paginate():
            clusters.extend(page["CacheClusters"])

        # Fetch cluster details concurrently
        tasks = [
            fetch_cluster_details_async(cluster, elasticache_client) for cluster in clusters
        ]
        detailed_clusters = await asyncio.gather(*tasks)
        return [cluster for cluster in detailed_clusters if cluster]
    except Exception as e:
        logging.error(f"Failed to get ElastiCache clusters: {e}")
        return []

# Aggregating results by VSAD level
def aggregate_vsad_data(clusters):
    """
    Aggregates cluster information at the VSAD level.
    """
    vsad_data = {}
    for cluster in clusters:
        vsad = cluster["VSAD"]
        if vsad not in vsad_data:
            vsad_data[vsad] = {
                "VSAD": vsad,
                "Count": 0,
                "Instances": [],
            }
        vsad_data[vsad]["Count"] += 1
        vsad_data[vsad]["Instances"].append(cluster)

    return list(vsad_data.values())

# FastAPI endpoint to fetch ElastiCache clusters
@app.get("/elasticache/clusters")
async def get_clusters(region: str):
    """
    Endpoint to fetch ElastiCache clusters by region.
    """
    try:
        clusters = await get_elasticache_clusters_async(region)
        if not clusters:
            raise HTTPException(status_code=404, detail="No clusters found")

        vsad_summary = aggregate_vsad_data(clusters)
        return vsad_summary
    except Exception as e:
        logging.error(f"Error fetching clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ElastiCache clusters")







import asyncio

async def fetch_cluster_tags_async(cluster_arn, elasticache_client):
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                response = await asyncio.to_thread(
                    elasticache_client.list_tags_for_resource, ResourceName=cluster_arn
                )
                tags = response.get("TagList", [])
                return {tag["Key"]: tag["Value"] for tag in tags}
            except Exception as e:
                if "Throttling" in str(e) or "Rate exceeded" in str(e):
                    await asyncio.sleep((2 ** attempt) + (time.time() % 1))
                else:
                    logging.error(f"Error fetching tags for {cluster_arn}: {e}")
                    break
        raise Exception(f"Max retries exceeded for {cluster_arn}")



from collections import defaultdict

def aggregate_by_vsad(cluster_details):
    """
    Aggregates cluster details at the VSAD level into a list of dictionaries.
    """
    vsad_info = defaultdict(lambda: {"Count": 0, "Instances": []})

    for cluster in cluster_details:
        vsad = cluster.get('VSAD', 'Unknown')
        vsad_info[vsad]["Count"] += 1
        vsad_info[vsad]["Instances"].append(cluster)

    # Convert to list of dictionaries
    vsad_list = [
        {"vsad": vsad, "Count": details["Count"], "Instances": details["Instances"]}
        for vsad, details in vsad_info.items()
    ]
    return vsad_list


from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import boto3
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError

app = FastAPI()

# Constants
MAX_ATTEMPTS = 5
BASE_DELAY = 1
MAX_DELAY = 30
THREADS = 10

def get_boto3_config(cluster_env, region):
    """
    Placeholder for custom boto3 configuration based on the environment and region.
    Modify this to suit your setup.
    """
    return boto3.Config(retries={'max_attempts': 10, 'mode': 'standard'})

def fetch_elasticache_clusters(region: str, cluster_env: str) -> Dict[str, Any]:
    """
    Fetches ElastiCache clusters and shard/node details.
    """
    session = boto3.Session()
    aws_boto_config = get_boto3_config(cluster_env, region)
    elasticache_client = session.client('elasticache', config=aws_boto_config, region_name=region)

    def exponential_backoff_retry(func, *args, **kwargs):
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return func(*args, **kwargs)
            except ClientError as ex:
                error_code = ex.response['Error']['Code']
                if error_code in ['ThrottlingException', 'RequestLimitExceeded']:
                    wait_time = min(MAX_DELAY, BASE_DELAY * (2 ** attempt) + random.uniform(0, 1))
                    time.sleep(wait_time)
                else:
                    raise ex
            except Exception as e:
                if attempt == MAX_ATTEMPTS:
                    raise e
        return None

    def get_cluster_tags(cluster_arn):
        return exponential_backoff_retry(
            elasticache_client.list_tags_for_resource,
            ResourceName=cluster_arn
        ).get("TagList", [])

    def fetch_cluster_details(cluster):
        cluster_id = cluster['CacheClusterId']
        cluster_arn = cluster['ARN']
        tags = get_cluster_tags(cluster_arn)
        tags_dict = {tag['Key']: tag['Value'] for tag in tags}
        creation_time = cluster.get('CacheClusterCreateTime', None)
        return {
            'ClusterName': cluster_id,
            'ClusterARN': cluster_arn,
            'Engine': cluster['Engine'],
            'NumOfCacheNodes': cluster['NumCacheNodes'],
            'CacheNodeType': cluster['CacheNodeType'],
            'CreationTime': creation_time.isoformat() if creation_time else None,
            'Tags': tags_dict,
            'VSAD': tags_dict.get('VSAD', 'Unknown')
        }

    def fetch_replication_group_shards():
        replication_groups = exponential_backoff_retry(elasticache_client.describe_replication_groups).get("ReplicationGroups", [])
        total_shards = sum(len(group["NodeGroups"]) for group in replication_groups)
        return total_shards

    clusters = []
    paginator = elasticache_client.get_paginator("describe_cache_clusters")
    for page in exponential_backoff_retry(paginator.paginate):
        clusters.extend(page['CacheClusters'])

    cluster_details = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(fetch_cluster_details, cluster) for cluster in clusters]
        for future in as_completed(futures):
            try:
                cluster_details.append(future.result())
            except Exception as e:
                print(f"Error fetching cluster details: {e}")

    total_shards = fetch_replication_group_shards()
    total_nodes = sum(cluster['NumCacheNodes'] for cluster in clusters)

    return {
        'Clusters': cluster_details,
        'Summary': {
            'TotalShards': total_shards,
            'TotalNodes': total_nodes
        }
    }

@app.get("/elasticache")
def get_elasticache(region: str, cluster_env: str):
    """
    API endpoint to fetch ElastiCache details.
    """
    try:
        data = fetch_elasticache_clusters(region, cluster_env)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





from fastapi import FastAPI, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from collections import defaultdict

app = FastAPI()

def get_tag_value(tags, key):
    return next((tag['Value'] for tag in tags if tag['Key'] == key), None)

def count_by_tg(instances, tag_key='tg'):
    tg_counts = defaultdict(int)
    for instance in instances:
        tags = instance.get('Tags', [])
        tg_value = get_tag_value(tags, tag_key)
        if tg_value:
            tg_counts[tg_value] += 1
    return tg_counts

@app.get("/ec2-instance-count-by-tg")
async def get_ec2_instance_count_by_tg():
    try:
        response = ec2_client.describe_instances()
        instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rds-instance-count-by-tg")
async def get_rds_instance_count_by_tg():
    try:
        response = rds_client.describe_db_instances()
        instances = response['DBInstances']
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opensearch-domain-count-by-tg")
async def get_opensearch_domain_count_by_tg():
    try:
        response = opensearch_client.list_domain_names()
        instances = [opensearch_client.describe_domain(DomainName=domain['DomainName'])['DomainStatus'] for domain in response['DomainNames']]
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/eks-cluster-count-by-tg")
async def get_eks_cluster_count_by_tg():
    try:
        response = eks_client.list_clusters()
        instances = [{'Tags': eks_client.list_tags_for_resource(resourceArn=arn)['tags']} for arn in response['clusters']]
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elasticache-cluster-count-by-tg")
async def get_elasticache_cluster_count_by_tg():
    try:
        response = elasticache_client.describe_cache_clusters()
        instances = response['CacheClusters']
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/s3-bucket-count-by-tg")
async def get_s3_bucket_count_by_tg():
    try:
        response = s3_client.list_buckets()
        instances = [{'Tags': s3_client.get_bucket_tagging(Bucket=bucket['Name'])['TagSet']} for bucket in response['Buckets']]
        tg_counts = count_by_tg(instances)
        return tg_counts
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




from fastapi import FastAPI, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os

app = FastAPI()

# Configure AWS credentials (can also be done via environment variables or AWS config file)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')  # Set your default region

# Create boto3 clients for the required AWS services
opensearch_client = boto3.client('opensearch', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
elasticache_client = boto3.client('elasticache', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

@app.get("/opensearch-domain-count")
async def get_opensearch_domain_count():
    try:
        paginator = opensearch_client.get_paginator('list_domain_names')
        domain_count = sum(len(page['DomainNames']) for page in paginator.paginate())
        return {"opensearch_domain_count": domain_count}
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elasticache-cluster-count")
async def get_elasticache_cluster_count():
    try:
        paginator = elasticache_client.get_paginator('describe_cache_clusters')
        cluster_count = sum(len(page['CacheClusters']) for page in paginator.paginate())
        return {"elasticache_cluster_count": cluster_count}
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)







import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os

# Configure AWS credentials (can also be done via environment variables or AWS config file)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')  # Set your default region

# Create boto3 client for CloudWatch
cloudwatch_client = boto3.client('cloudwatch', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

def get_elasticache_cluster_count():
    try:
        paginator = cloudwatch_client.get_paginator('list_metrics')
        response_iterator = paginator.paginate(
            Namespace='AWS/ElastiCache',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'CacheClusterId'}]
        )

        cluster_ids = set()
        for page in response_iterator:
            for metric in page['Metrics']:
                for dimension in metric['Dimensions']:
                    if dimension['Name'] == 'CacheClusterId':
                        cluster_ids.add(dimension['Value'])
        
        cluster_count = len(cluster_ids)
        return {"elasticache_cluster_count": cluster_count}
    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
    except PartialCredentialsError:
        return {"error": "Incomplete AWS credentials"}
    except Exception as e:
        return {"error": str(e)}



import boto3
from fastapi import HTTPException
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, EndpointConnectionError
from .circuit_breaker import breaker

@breaker
def get_s3_bucket_count_by_region(region: str):
    session = boto3.Session()
    s3_client = session.client('s3', region_name=region)
    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']
        count = 0
        for bucket in buckets:
            bucket_location = s3_client.get_bucket_location(Bucket=bucket['Name'])['LocationConstraint']
            if bucket_location == region:
                count += 1
        return {"s3_bucket_count": count}
    except NoCredentialsError:
        raise HTTPException(status_code=400, detail="AWS credentials not found")
    except PartialCredentialsError:
        raise HTTPException(status_code=400, detail="Incomplete AWS credentials")
    except EndpointConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Endpoint connection error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        s3_client.close()

import boto3
from collections import defaultdict

def get_eks_clusters_count_by_vsad():
    eks_client = boto3.client('eks')
    paginator = eks_client.get_paginator('list_clusters')
    cluster_iterator = paginator.paginate()
    
    vsad_counts = defaultdict(int)
    
    for cluster_page in cluster_iterator:
        cluster_names = cluster_page['clusters']
        
        for cluster_name in cluster_names:
            cluster_info = eks_client.describe_cluster(name=cluster_name)
            tags = cluster_info['cluster']['tags']
            
            vsad = tags.get('vsad')
            if vsad:
                vsad_counts[vsad] += 1
    
    return vsad_counts






import boto3
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from fastapi import HTTPException

# Constants
MAX_ATTEMPTS = 5
BASE_DELAY = 1
MAX_DELAY = 30
THREADS = 10  # Number of parallel threads for processing

def fetch_elasticache_clusters(region, cluster_env):
    """
    Fetches ElastiCache cluster details with retries, exponential backoff, and parallel processing.
    """
    session = boto3.Session()
    aws_boto_config = get_boto3_config(cluster_env, region)
    elasticache_client = session.client('elasticache', config=aws_boto_config, region_name=region)

    def exponential_backoff_retry(func, *args, **kwargs):
        """
        Helper function to retry operations with exponential backoff and jitter.
        """
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return func(*args, **kwargs)
            except ClientError as ex:
                error_code = ex.response['Error']['Code']
                if error_code in ['ThrottlingException', 'RequestLimitExceeded']:
                    wait_time = min(MAX_DELAY, BASE_DELAY * (2 ** attempt) + random.uniform(0, 1))
                    print(f"Retrying in {wait_time:.2f} seconds (Attempt {attempt}) due to throttling...")
                    time.sleep(wait_time)
                else:
                    raise ex
            except Exception as e:
                if attempt == MAX_ATTEMPTS:
                    raise e
        return None

    def get_cluster_tags(cluster_arn):
        """
        Fetches tags for a given cluster ARN.
        """
        return exponential_backoff_retry(
            elasticache_client.list_tags_for_resource,
            ResourceName=cluster_arn
        ).get("TagList", [])

    def fetch_cluster_details(cluster):
        """
        Fetches details for a single cluster, including tags and creation time.
        """
        cluster_id = cluster['CacheClusterId']
        cluster_arn = cluster['ARN']
        tags = get_cluster_tags(cluster_arn)
        tags_dict = {tag['Key']: tag['Value'] for tag in tags}
        creation_time = cluster.get('CacheClusterCreateTime', None)
        return {
            'ClusterName': cluster_id,
            'ClusterARN': cluster_arn,
            'Engine': cluster['Engine'],
            'NumOfCacheNodes': cluster['NumCacheNodes'],
            'CacheNodeType': cluster['CacheNodeType'],
            'CreationTime': creation_time.isoformat() if creation_time else None,
            'Tags': tags_dict,
            'VSAD': tags_dict.get('VSAD', 'Unknown')
        }

    def fetch_replication_group_shards():
        """
        Fetches details for shards and replication groups.
        """
        replication_groups = exponential_backoff_retry(elasticache_client.describe_replication_groups).get("ReplicationGroups", [])
        total_shards = sum(len(group["NodeGroups"]) for group in replication_groups)
        return total_shards

    # Fetch cluster data
    clusters = []
    paginator = elasticache_client.get_paginator("describe_cache_clusters")
    for page in exponential_backoff_retry(paginator.paginate):
        clusters.extend(page['CacheClusters'])

    # Use threads to process clusters in parallel
    cluster_details = []
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = [executor.submit(fetch_cluster_details, cluster) for cluster in clusters]
        for future in as_completed(futures):
            try:
                cluster_details.append(future.result())
            except Exception as e:
                print(f"Error fetching cluster details: {e}")

    # Fetch shard details
    total_shards = fetch_replication_group_shards()
    total_nodes = sum(cluster['NumCacheNodes'] for cluster in clusters)

    return {
        'Clusters': cluster_details,
        'Summary': {
            'TotalShards': total_shards,
            'TotalNodes': total_nodes
        }
    }
