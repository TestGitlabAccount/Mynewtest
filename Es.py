### Summary of API Endpoints

Here are the API endpoints you can now use:

1. **EKS Clusters**: `/eks/clusters`
2. **OpenSearch Domains**: `/opensearch/domains`
3. **ElastiCache Clusters**: `/elasticache/clusters`

### Complete FastAPI Application

Here is the complete code with all the endpoints integrated:

```python
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Define a request model for API calls
class AWSRequest(BaseModel):
    region: str

# Helper function to extract tag values
def extract_tag_value(tag_list: List[Dict[str, str]], key: str) -> str:
    for tag in tag_list:
        if tag.get('Key') == key:
            return tag.get('Value', 'Unknown')
    return 'Unknown'

# Fetch EKS Clusters grouped by VSAD
def fetch_eks_clusters_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('eks', region_name=region)
    clusters_by_vsad = {}  # Dictionary to hold clusters grouped by VSAD

    # Describe EKS Clusters
    paginator = client.get_paginator('list_clusters')
    for page in paginator.paginate():
        for cluster_name in page['clusters']:
            # Describe cluster to get detailed information including tags
            cluster = client.describe_cluster(name=cluster_name)['cluster']
            vsad = extract_tag_value(cluster.get('tags', []), 'VSAD')
            owner = extract_tag_value(cluster.get('tags', []), 'owner')
            cluster_info = {
                "instanceType": cluster.get('version', 'Unknown'),  # EKS doesn't have instanceType; using version instead
                "owner": owner,
                "creationdate": cluster.get('createdAt').strftime('%Y-%m-%d'),
                "ResourceID": cluster.get('arn')
            }
            if vsad not in clusters_by_vsad:
                clusters_by_vsad[vsad] = []  # Initialize with an empty list
            clusters_by_vsad[vsad].append(cluster_info)

    # Format the response
    formatted_clusters = [{"vsad": vsad, "Count": len(clusters), "instances": clusters} for vsad, clusters in clusters_by_vsad.items()]
    
    return formatted_clusters

@app.post("/eks/clusters")
async def get_eks_clusters_by_vsad(request: AWSRequest):
    try:
        clusters_by_vsad = fetch_eks_clusters_by_vsad(request.region)

        if not clusters_by_vsad:
            return {"message": "No EKS clusters found for the specified region."}

        response = {"clusters": clusters_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Fetch OpenSearch Domains grouped by VSAD
def fetch_opensearch_domains_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('opensearch', region_name=region)
    domains_by_vsad = {}  # Dictionary to hold domains grouped by VSAD

    # List OpenSearch Domains
    domain_names = client.list_domain_names()['DomainNames']
    for domain_name in domain_names:
        domain_info = client.describe_domain(DomainName=domain_name['DomainName'])['DomainStatus']
        vsad = extract_tag_value(domain_info.get('Tags', []), 'VSAD')
        owner = extract_tag_value(domain_info.get('Tags', []), 'owner')
        domain_info_dict = {
            "instanceType": domain_info.get('InstanceType', 'Unknown'),
            "owner": owner,
            "creationdate": domain_info.get('CreatedAt').strftime('%Y-%m-%d') if 'CreatedAt' in domain_info else 'Unknown',
            "ResourceID": domain_info.get('ARN')
        }
        if vsad not in domains_by_vsad:
            domains_by_vsad[vsad] = []  # Initialize with an empty list
        domains_by_vsad[vsad].append(domain_info_dict)

    # Format the response
    formatted_domains = [{"vsad": vsad, "Count": len(domains), "instances": domains} for vsad, domains in domains_by_vsad.items()]

    return formatted_domains

@app.post("/opensearch/domains")
async def get_opensearch_domains_by_vsad(request: AWSRequest):
    try:
        domains_by_vsad = fetch_opensearch_domains_by_vsad(request.region)

        if not domains_by_vsad:
            return {"message": "No OpenSearch domains found for the specified region."}

        response = {"clusters": domains_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Fetch ElastiCache Clusters grouped by VSAD
def fetch_elasticache_clusters_by_vsad(region: str) -> List[Dict[str, Any]]:
    client = boto3.client('elasticache', region_name=region)
    clusters_by_vsad = {}  # Dictionary to hold clusters grouped by VSAD

    # Describe ElastiCache Clusters
    paginator = client.get_paginator('describe_cache_clusters')
    for page in paginator.paginate():
        for cluster in page['CacheClusters']:
            vsad = extract_tag_value(cluster.get('Tags', []), 'VSAD')
            owner = extract_tag_value(cluster.get('Tags', []), 'owner')
            cluster_info = {
                "instanceType": cluster.get('CacheNodeType', 'Unknown'),
                "owner": owner,
                "creationdate": cluster.get('CacheClusterCreateTime').strftime('%Y-%m-%d'),
                "ResourceID": cluster.get('ARN')
            }
            if vsad not in clusters_by_vsad:
                clusters_by_vsad[vsad] = []  # Initialize with an empty list
            clusters_by_vsad[vsad].append(cluster_info)

    # Format the response
    formatted_clusters = [{"vsad": vsad, "Count": len(clusters), "instances": clusters} for vsad, clusters in clusters_by_vsad.items()]

    return formatted_clusters

@app.post("/elasticache/clusters")
async def get_elasticache_clusters_by_vsad(request: AWSRequest):
    try:
        clusters_by_vsad = fetch_elasticache_clusters_by_vsad(request.region)

        if not clusters_by_vsad:
            return {"message": "No ElastiCache clusters found for the specified region."}

        response = {"clusters": clusters_by_vsad}
        return response
    except ClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
