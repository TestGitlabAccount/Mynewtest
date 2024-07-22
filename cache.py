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
