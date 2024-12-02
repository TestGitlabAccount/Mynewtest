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
