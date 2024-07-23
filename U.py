import boto3

def get_all_target_groups(client):
    """Retrieve all target groups in the specified region."""
    target_groups = []
    paginator = client.get_paginator('describe_target_groups')
    
    for page in paginator.paginate():
        target_groups.extend(page['TargetGroups'])
    
    return target_groups

def is_target_group_used(client, target_group_arn):
    """Check if the target group is associated with any load balancers."""
    response = client.describe_target_group_attributes(
        TargetGroupArn=target_group_arn
    )
    
    return len(response.get('Attributes', [])) > 0

def get_unused_target_groups(client):
    """Find unused target groups related to EKS."""
    unused_target_groups = []
    target_groups = get_all_target_groups(client)
    
    for tg in target_groups:
        tg_arn = tg['TargetGroupArn']
        tg_name = tg['TargetGroupName']
        tags = client.describe_tags(
            ResourceArns=[tg_arn]
        ).get('TagDescriptions', [])

        # Check for EKS-related tags or naming conventions
        is_eks_target_group = any(
            tag['Key'].startswith('eks:') or 'eks' in tg_name.lower()
            for tag in tags[0]['Tags']
        )

        if is_eks_target_group:
            if not is_target_group_used(client, tg_arn):
                unused_target_groups.append({
                    'TargetGroupArn': tg_arn,
                    'TargetGroupName': tg_name,
                    'OwnerId': tg['LoadBalancerArns'],
                })

    return unused_target_groups

def main():
    # Create a boto3 client for Elastic Load Balancing
    client = boto3.client('elbv2', region_name='us-west-2')  # Change to your region
    
    # Get unused target groups
    unused_target_groups = get_unused_target_groups(client)
    
    # Print the unused target groups with their owner IDs
    if unused_target_groups:
        print("Unused EKS Target Groups:")
        for tg in unused_target_groups:
            print(f"Name: {tg['TargetGroupName']}, Arn: {tg['TargetGroupArn']}, Owner: {tg['OwnerId']}")
    else:
        print("No unused EKS target groups found.")

if __name__ == "__main__":
    main()
