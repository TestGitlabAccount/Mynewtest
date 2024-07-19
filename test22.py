from fastapi import FastAPI, HTTPException
from aws.rdsMethods import group_rds_clusters_by_vsad, group_rds_instances_by_vsad
from aws.mskMethods import group_msk_clusters_by_vsad
from aws.elasticacheMethods import group_elasticache_clusters_by_vsad
from aws.opensearchMethods import group_opensearch_domains_by_vsad

app = FastAPI()

@app.get("/rds/clusters")
async def get_rds_clusters_by_vsad():
    try:
        vsad_groups = group_rds_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rds/instances")
async def get_rds_instances_by_vsad():
    try:
        vsad_groups = group_rds_instances_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/msk/clusters")
async def get_msk_clusters_by_vsad():
    try:
        vsad_groups = group_msk_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elasticache/clusters")
async def get_elasticache_clusters_by_vsad():
    try:
        vsad_groups = group_elasticache_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opensearch/domains")
async def get_opensearch_domains_by_vsad():
    try:
        vsad_groups = group_opensearch_domains_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



import boto3

def get_vsad_tag(tags):
    for tag in tags:
        if tag['Key'] == 'Vsad':
            return tag['Value']
    return None

def group_by_vsad(instances):
    vsad_group = {}
    for instance in instances:
        vsad = get_vsad_tag(instance.get('Tags', []))
        if vsad:
            if vsad not in vsad_group:
                vsad_group[vsad] = {
                    'count': 0,
                    'instances': []
                }
            vsad_group[vsad]['count'] += 1
            vsad_group[vsad]['instances'].append(instance)
    return vsad_group



import boto3
from .helpers import get_vsad_tag, group_by_vsad

def get_rds_clusters():
    rds_client = boto3.client('rds')
    clusters = []
    paginator = rds_client.get_paginator('describe_db_clusters')
    for page in paginator.paginate():
        clusters.extend(page['DBClusters'])
    return clusters

def get_rds_instances():
    rds_client = boto3.client('rds')
    instances = []
    paginator = rds_client.get_paginator('describe_db_instances')
    for page in paginator.paginate():
        instances.extend(page['DBInstances'])
    return instances

def group_rds_clusters_by_vsad():
    clusters = get_rds_clusters()
    return group_by_vsad(clusters)

def group_rds_instances_by_vsad():
    instances = get_rds_instances()
    return group_by_vsad(instances)


import boto3
from .helpers import get_vsad_tag, group_by_vsad

def get_msk_clusters():
    msk_client = boto3.client('kafka')
    clusters = []
    paginator = msk_client.get_paginator('list_clusters')
    for page in paginator.paginate():
        for cluster in page['ClusterInfoList']:
            clusters.append(cluster)
    return clusters

def group_msk_clusters_by_vsad():
    clusters = get_msk_clusters()
    return group_by_vsad(clusters)



import boto3
from .helpers import get_vsad_tag, group_by_vsad

def get_elasticache_clusters():
    elasticache_client = boto3.client('elasticache')
    clusters = []
    paginator = elasticache_client.get_paginator('describe_cache_clusters')
    for page in paginator.paginate():
        clusters.extend(page['CacheClusters'])
    return clusters

def group_elasticache_clusters_by_vsad():
    clusters = get_elasticache_clusters()
    return group_by_vsad(clusters)


import boto3
from .helpers import get_vsad_tag, group_by_vsad

def get_opensearch_domains():
    opensearch_client = boto3.client('opensearch')
    domains = []
    paginator = opensearch_client.get_paginator('list_domain_names')
    for page in paginator.paginate():
        for domain_info in page['DomainNames']:
            domain_name = domain_info['DomainName']
            domain_details = opensearch_client.describe_domain(DomainName=domain_name)
            domains.append(domain_details['DomainStatus'])
    return domains

def group_opensearch_domains_by_vsad():
    domains = get_opensearch_domains()
    return group_by_vsad(domains)


from fastapi import FastAPI, HTTPException
from aws.rdsMethods import group_rds_clusters_by_vsad, group_rds_instances_by_vsad
from aws.mskMethods import group_msk_clusters_by_vsad
from aws.elasticacheMethods import group_elasticache_clusters_by_vsad
from aws.opensearchMethods import group_opensearch_domains_by_vsad

app = FastAPI()

@app.get("/rds/clusters")
async def get_rds_clusters_by_vsad():
    try:
        vsad_groups = group_rds_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rds/instances")
async def get_rds_instances_by_vsad():
    try:
        vsad_groups = group_rds_instances_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/msk/clusters")
async def get_msk_clusters_by_vsad():
    try:
        vsad_groups = group_msk_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/elasticache/clusters")
async def get_elasticache_clusters_by_vsad():
    try:
        vsad_groups = group_elasticache_clusters_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opensearch/domains")
async def get_opensearch_domains_by_vsad():
    try:
        vsad_groups = group_opensearch_domains_by_vsad()
        return vsad_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



import boto3

def get_opensearch_domains():
    es_client = boto3.client('opensearch')
    domains = []
    paginator = es_client.get_paginator('list_domain_names')

    for page in paginator.paginate():
        domains.extend(page['DomainNames'])

    # Add tags to each domain
    for domain in domains:
        domain_name = domain['DomainName']
        domain_arn = es_client.describe_domain(DomainName=domain_name)['DomainStatus']['ARN']
        tags_response = es_client.list_tags(ARN=domain_arn)
        domain['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}

    return domains

def group_opensearch_domains_by_vsad():
    domains = get_opensearch_domains()
    vsad_counts = {}
    for domain in domains:
        tags = domain.get('Tags', {})
        vsad = tags.get('Vsad', None)
        if vsad:
            if vsad not in vsad_counts:
                vsad_counts[vsad] = {
                    "count": 0,
                    "instance_details": []
                }
            vsad_counts[vsad]["count"] += 1
            vsad_counts[vsad]["instance_details"].append({
                "ID": domain['DomainName'],
                "instanceType": "opensearch",
                "Vsad": vsad
            })

    return {
        "totalnewinstances": len(domains),
        "vsadlevel": vsad_counts
    }



import boto3
from fastapi import HTTPException

def get_elasticache_clusters():
    es_client = boto3.client('elasticache')
    clusters = []
    paginator = es_client.get_paginator('describe_cache_clusters')
    for page in paginator.paginate():
        clusters.extend(page['CacheClusters'])
    
    detailed_clusters = []
    
    for cluster in clusters:
        cluster_arn = cluster['ARN']
        
        # Get tags for the cluster
        tags_response = es_client.list_tags_for_resource(ResourceName=cluster_arn)
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagList']}
        
        # Append detailed cluster info
        detailed_clusters.append({
            'CacheClusterId': cluster['CacheClusterId'],
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
                    vsad_counts[vsad] = {
                        "count": 0,
                        "instance_details": []
                    }
                vsad_counts[vsad]["count"] += 1
                vsad_counts[vsad]["instance_details"].append({
                    "ID": cluster['CacheClusterId'],
                    "instanceType": "elasticache",
                    "Vsad": vsad
                })

        return {
            "totalnewinstances": len(clusters),
            "vsadlevel": vsad_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

