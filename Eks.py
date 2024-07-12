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
