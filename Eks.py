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
from datetime import datetime

def get_msk_details(region: str, environment: str):
    # Initialize Boto3 client for MSK
    client = boto3.client('kafka', region_name=region)

    # Retrieve the list of clusters
    clusters = client.list_clusters()

    # Prepare a dictionary to store VSAD information
    vsad_data = {}

    # Iterate over each cluster and describe them
    for cluster_arn in clusters['ClusterInfoList']:
        cluster_info = client.describe_cluster(ClusterArn=cluster_arn['ClusterArn'])
        
        # Extract the tags for each cluster
        tags = client.list_tags_for_resource(ResourceArn=cluster_arn['ClusterArn'])
        
        vsad = None
        owner = None
        creationdate = None
        resource_id = cluster_info['ClusterInfo']['ClusterArn']
        
        # Process tags
        for key, value in tags['Tags'].items():
            if key.lower() == 'vsad':
                vsad = value
            elif key.lower() == 'owner':
                owner = value
            elif key.lower() == 'creationdate':
                creationdate = value

        # Only proceed if VSAD is present
        if vsad:
            # Initialize VSAD entry if not present
            if vsad not in vsad_data:
                vsad_data[vsad] = {
                    'vsad': vsad,
                    'Count': 0,
                    'instances': []
                }

            # Increment the count for this VSAD
            vsad_data[vsad]['Count'] += 1

            # Append the instance details
            vsad_data[vsad]['instances'].append({
                'instanceType': cluster_info['ClusterInfo']['ClusterType'],
                'owner': owner or 'Unknown',
                'creationdate': creationdate or 'Unknown',
                'ResourceID': resource_id
            })

    # Convert the vsad_data dictionary to a list
    vsad_list = [details for vsad, details in vsad_data.items()]
    return vsad_list

    ec2 = boto3.client('ec2')
    response = ec2.describe_snapshots(OwnerIds=['self'])  # 'self' refers to your account
    return len(response['Snapshots'])




from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Define a request model for API calls
class RDSRequest(BaseModel):
    region: str

# Define a helper function to extract tags from TagList
def extract_owner(tag_list: List[Dict[str, str]]) -> str:
    for tag in tag_list:
        if tag.get('Key') == 'owner':
            return tag.get('Value', 'Unknown')
    return 'Unknown'

# Function to fetch RDS Clusters using paginator
def fetch_rds_clusters(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('rds', region_name=region)

    clusters = []
    paginator = client.get_paginator('describe_db_clusters')

    for page in paginator.paginate():
        for cluster in page['DBClusters']:
            cluster_info = {
                "DBClusterIdentifier": cluster.get('DBClusterIdentifier'),
                "owner": extract_owner(cluster.get('TagList', [])),
                "creationdate": cluster.get('ClusterCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": cluster.get('DBClusterArn'),
                "Status": cluster.get('Status'),
                "Engine": cluster.get('Engine'),
                "EngineVersion": cluster.get('EngineVersion'),
                "StorageEncrypted": cluster.get('StorageEncrypted'),
                "AvailabilityZones": cluster.get('AvailabilityZones'),
                "BackupRetentionPeriod": cluster.get('BackupRetentionPeriod'),
                "Endpoint": cluster.get('Endpoint'),
                "ReaderEndpoint": cluster.get('ReaderEndpoint'),
                "DBClusterMembers": [{
                    "DBInstanceIdentifier": member.get('DBInstanceIdentifier'),
                    "IsClusterWriter": member.get('IsClusterWriter'),
                } for member in cluster.get('DBClusterMembers', [])],
                "VpcSecurityGroups": [{
                    "VpcSecurityGroupId": sg.get('VpcSecurityGroupId'),
                    "Status": sg.get('Status'),
                } for sg in cluster.get('VpcSecurityGroups', [])],
                "Tags": [{tag['Key']: tag['Value']} for tag in cluster.get('TagList', [])]
            }
            clusters.append(cluster_info)

    return clusters

# Function to fetch RDS Instances using paginator
def fetch_rds_instances(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('rds', region_name=region)

    instances = []
    paginator = client.get_paginator('describe_db_instances')

    for page in paginator.paginate():
        for instance in page['DBInstances']:
            instance_info = {
                "DBInstanceIdentifier": instance.get('DBInstanceIdentifier'),
                "owner": extract_owner(instance.get('TagList', [])),
                "creationdate": instance.get('InstanceCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": instance.get('DBInstanceArn'),
                "Status": instance.get('DBInstanceStatus'),
                "Engine": instance.get('Engine'),
                "EngineVersion": instance.get('EngineVersion'),
                "DBInstanceClass": instance.get('DBInstanceClass'),
                "MultiAZ": instance.get('MultiAZ'),
                "StorageType": instance.get('StorageType'),
                "VpcSecurityGroups": [{
                    "VpcSecurityGroupId": sg.get('VpcSecurityGroupId'),
                    "Status": sg.get('Status'),
                } for sg in instance.get('VpcSecurityGroups', [])],
                "Tags": [{tag['Key']: tag['Value']} for tag in instance.get('TagList', [])]
            }
            instances.append(instance_info)

    return instances

@app.post("/rds/clusters")
async def get_rds_clusters(request: RDSRequest):
    try:
        clusters = fetch_rds_clusters(request.region)
        if not clusters:
            return {"message": "No clusters found for the specified region."}

        response = {
            "clusters": clusters
        }

        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rds/instances")
async def get_rds_instances(request: RDSRequest):
    try:
        instances = fetch_rds_instances(request.region)
        if not instances:
            return {"message": "No instances found for the specified region."}

        response = {
            "instances": instances
        }

        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))




from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Define a request model for API calls
class RDSRequest(BaseModel):
    region: str

# Helper function to extract tag values
def extract_tag_value(tag_list: List[Dict[str, str]], key: str) -> str:
    for tag in tag_list:
        if tag.get('Key') == key:
            return tag.get('Value', 'Unknown')
    return 'Unknown'

# Fetch RDS Clusters and Instances grouped by VSAD
def fetch_rds_clusters_and_instances_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('rds', region_name=region)
    clusters_by_vsad = {}
    
    # Describe RDS Clusters
    paginator_clusters = client.get_paginator('describe_db_clusters')
    for page in paginator_clusters.paginate():
        for cluster in page['DBClusters']:
            vsad = extract_tag_value(cluster.get('TagList', []), 'VSAD')
            owner = extract_tag_value(cluster.get('TagList', []), 'owner')
            cluster_info = {
                "instanceType": cluster.get('DBClusterInstanceClass', 'Unknown'),
                "owner": owner,
                "creationdate": cluster.get('ClusterCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": cluster.get('DBClusterArn')
            }
            if vsad not in clusters_by_vsad:
                clusters_by_vsad[vsad] = []
            clusters_by_vsad[vsad].append(cluster_info)

    # Describe RDS Instances
    paginator_instances = client.get_paginator('describe_db_instances')
    for page in paginator_instances.paginate():
        for instance in page['DBInstances']:
            vsad = extract_tag_value(instance.get('TagList', []), 'VSAD')
            owner = extract_tag_value(instance.get('TagList', []), 'owner')
            instance_info = {
                "instanceType": instance.get('DBInstanceClass'),
                "owner": owner,
                "creationdate": instance.get('InstanceCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": instance.get('DBInstanceArn')
            }
            if vsad not in clusters_by_vsad:
                clusters_by_vsad[vsad] = []
            clusters_by_vsad[vsad].append(instance_info)

    # Format the output to match the required structure
    output = []
    for vsad, instances in clusters_by_vsad.items():
        output.append({
            "vsad": vsad,
            "Count": len(instances),
            "instances": instances
        })

    return output

@app.post("/rds/clusters-and-instances")
async def get_rds_clusters_and_instances_by_vsad(request: RDSRequest):
    try:
        clusters_and_instances_by_vsad = fetch_rds_clusters_and_instances_by_vsad(request.region)
        if not clusters_and_instances_by_vsad:
            return {"message": "No clusters or instances found for the specified region."}

        response = {"clusters": clusters_and_instances_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))










from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Define a request model for API calls
class RDSRequest(BaseModel):
    region: str

# Helper function to extract tag values
def extract_tag_value(tag_list: List[Dict[str, str]], key: str) -> str:
    for tag in tag_list:
        if tag.get('Key') == key:
            return tag.get('Value', 'Unknown')
    return 'Unknown'

# Fetch RDS Clusters grouped by VSAD
def fetch_rds_clusters_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('rds', region_name=region)
    clusters_by_vsad = {}

    # Describe RDS Clusters
    paginator_clusters = client.get_paginator('describe_db_clusters')
    for page in paginator_clusters.paginate():
        for cluster in page['DBClusters']:
            vsad = extract_tag_value(cluster.get('TagList', []), 'VSAD')
            owner = extract_tag_value(cluster.get('TagList', []), 'owner')
            cluster_info = {
                "instanceType": cluster.get('DBClusterInstanceClass', 'Unknown'),
                "owner": owner,
                "creationdate": cluster.get('ClusterCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": cluster.get('DBClusterArn')
            }
            if vsad not in clusters_by_vsad:
                clusters_by_vsad[vsad] = []
            clusters_by_vsad[vsad].append(cluster_info)

    # Format the response
    formatted_clusters = [{"vsad": vsad, "Count": len(clusters), "instances": clusters} for vsad, clusters in clusters_by_vsad.items()]
    
    return formatted_clusters

# Fetch RDS Instances grouped by VSAD
def fetch_rds_instances_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('rds', region_name=region)
    instances_by_vsad = {}

    # Describe RDS Instances
    paginator_instances = client.get_paginator('describe_db_instances')
    for page in paginator_instances.paginate():
        for instance in page['DBInstances']:
            vsad = extract_tag_value(instance.get('TagList', []), 'VSAD')
            owner = extract_tag_value(instance.get('TagList', []), 'owner')
            instance_info = {
                "instanceType": instance.get('DBInstanceClass'),
                "owner": owner,
                "creationdate": instance.get('InstanceCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": instance.get('DBInstanceArn')
            }
            if vsad not in instances_by_vsad:
                instances_by_vsad[vsad] = []
            instances_by_vsad[vsad].append(instance_info)

    # Format the response
    formatted_instances = [{"vsad": vsad, "Count": len(instances), "instances": instances} for vsad, instances in instances_by_vsad.items()]

    return formatted_instances

@app.post("/rds/clusters")
async def get_rds_clusters_by_vsad(request: RDSRequest):
    try:
        clusters_by_vsad = fetch_rds_clusters_by_vsad(request.region)

        if not clusters_by_vsad:
            return {"message": "No clusters found for the specified region."}

        response = {"clusters": clusters_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rds/instances")
async def get_rds_instances_by_vsad(request: RDSRequest):
    try:
        instances_by_vsad = fetch_rds_instances_by_vsad(request.region)

        if not instances_by_vsad:
            return {"message": "No instances found for the specified region."}

        response = {"instances": instances_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Example Run Command
# uvicorn main:app --reload --host 0.0.0.0 --port 8000




