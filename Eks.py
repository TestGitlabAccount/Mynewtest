import boto3
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_eks_clusters_count_by_vsad():
    eks_client = boto3.client('eks')
    vsad_counts = defaultdict(int)
    next_token = None

    while True:
        if next_token:
            response = eks_client.list_clusters(nextToken=next_token)
        else:
            response = eks_client.list_clusters()
        
        cluster_names = response.get('clusters', [])
        next_token = response.get('nextToken')

        logger.debug(f"Processing clusters: {cluster_names}")

        for cluster_name in cluster_names:
            cluster_info = eks_client.describe_cluster(name=cluster_name)
            tags = cluster_info['cluster'].get('tags', {})
            logger.debug(f"Cluster: {cluster_name}, Tags: {tags}")
            
            vsad = tags.get('vsad')
            if vsad:
                vsad_counts[vsad] += 1
        
        if not next_token:
            break

    logger.debug(f"VSAD counts: {vsad_counts}")
    return vsad_counts





from fastapi import FastAPI
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os

app = FastAPI()

# Configure AWS credentials (can also be done via environment variables or AWS config file)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')  # Set your default region

# Create a boto3 EC2 client
ec2_client = boto3.client(
    'ec2',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

@app.get("/ec2-instance-count")
async def get_ec2_instance_count():
    try:
        # Describe EC2 instances
        response = ec2_client.describe_instances()
        instances = response['Reservations']
        
        # Count the instances
        instance_count = sum(len(reservation['Instances']) for reservation in instances)
        return {"instance_count": instance_count}

    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
    except PartialCredentialsError:
        return {"error": "Incomplete AWS credentials"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



import boto3
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_elasticache_clusters_count_by_vsad():
    elasticache_client = boto3.client('elasticache')
    vsad_counts = defaultdict(int)
    next_token = None

    while True:
        if next_token:
            response = elasticache_client.describe_cache_clusters(Marker=next_token)
        else:
            response = elasticache_client.describe_cache_clusters()
        
        clusters = response.get('CacheClusters', [])
        next_token = response.get('Marker')

        logger.debug(f"Processing clusters: {clusters}")

        for cluster in clusters:
            cache_cluster_id = cluster['CacheClusterId']
            tags_response = elasticache_client.list_tags_for_resource(
                ResourceName=f'arn:aws:elasticache:{cluster["CacheClusterId"]}'
            )
            tags = tags_response.get('TagList', [])
            tag_dict = {tag['Key']: tag['Value'] for tag in tags}
            logger.debug(f"Cluster: {cache_cluster_id}, Tags: {tag_dict}")
            
            vsad = tag_dict.get('vsad')
            if vsad:
                vsad_counts[vsad] += 1
        
        if not next_token:
            break

    logger.debug(f"VSAD counts: {vsad_counts}")
    print(vsad_counts)  # Print the vsad_counts dictionary
    return vsad_counts




from fastapi import FastAPI
from aws.aws_methods import get_ebs_volumes_count, get_snapshots_count

app = FastAPI()

@app.get("/ebs_volumes_count")
def ebs_volumes_count():
    count = get_ebs_volumes_count()
    return {"EBS Volumes Count": count}

@app.get("/snapshots_count")
def snapshots_count():
    count = get_snapshots_count()
    return {"Snapshots Count": count}


import boto3

def get_ebs_volumes_count():
    ec2 = boto3.client('ec2')
    response = ec2.describe_volumes()
    return len(response['Volumes'])

def get_snapshots_count():
    ec2 = boto3.client('ec2')
    response = ec2.describe_snapshots(OwnerIds=['self'])  # 'self' refers to your account
    return len(response['Snapshots'])

