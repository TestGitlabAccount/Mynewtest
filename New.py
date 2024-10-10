import boto3

def get_alb_tags_by_vsad():
    # Create a Boto3 client for ELBv2 (ALBs)
    client = boto3.client('elbv2')

    # Step 1: Retrieve all ALBs
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    # Step 2: Iterate over each ALB to retrieve its tags
    for lb in load_balancers:
        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']

        # Step 3: Get the tags for the ALB using its ARN
        tags_response = client.describe_tags(
            ResourceArns=[lb_arn]
        )
        
        # Step 4: Extract tags into a dictionary
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        
        # Step 5: Get the VSAD tag value if it exists
        vsad = tags.get('VSAD')

        # If VSAD tag is found, group the ALB data under the corresponding VSAD key
        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []

            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })
    
    return vsad_data

# Example usage
if __name__ == '__main__':
    vsad_data = get_alb_tags_by_vsad()
    
    for vsad, albs in vsad_data.items():
        print(f"VSAD: {vsad}")
        for alb in albs:
            print(f"  ALB Name: {alb['LoadBalancerName']}")
            print(f"  ALB ARN: {alb['LoadBalancerArn']}")
            print(f"  Tags: {alb['Tags']}")
        print("\n")





import boto3

def get_alb_tags_by_vsad():
    client = boto3.client('elbv2')
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    for lb in load_balancers:
        if lb['Type'] != 'application':  # Filter only ALBs
            continue

        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']
        tags_response = client.describe_tags(ResourceArns=[lb_arn])
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        vsad = tags.get('VSAD')

        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []
            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })

    return vsad_data


def get_nlb_tags_by_vsad():
    client = boto3.client('elbv2')
    response = client.describe_load_balancers()
    load_balancers = response['LoadBalancers']

    vsad_data = {}

    for lb in load_balancers:
        if lb['Type'] != 'network':  # Filter only NLBs
            continue

        lb_name = lb['LoadBalancerName']
        lb_arn = lb['LoadBalancerArn']
        tags_response = client.describe_tags(ResourceArns=[lb_arn])
        tags = {tag['Key']: tag['Value'] for tag in tags_response['TagDescriptions'][0]['Tags']}
        vsad = tags.get('VSAD')

        if vsad:
            if vsad not in vsad_data:
                vsad_data[vsad] = []
            vsad_data[vsad].append({
                'LoadBalancerName': lb_name,
                'LoadBalancerArn': lb_arn,
                'Tags': tags
            })

    return vsad_data
