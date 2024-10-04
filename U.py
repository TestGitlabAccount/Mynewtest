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


import boto3

# Initialize a session using AWS credentials
client = boto3.client('support', region_name='us-east-1')  # AWS Support API is only available in 'us-east-1'

# Define the number of cases you want to retrieve
max_results = 5

# Get the list of support cases
response = client.describe_cases(
    includeResolvedCases=False,  # Exclude resolved cases
    maxResults=max_results        # Limit the number of cases retrieved
)

# Extract and print details of the cases
cases = response.get('cases', [])

if cases:
    print(f"Displaying the first {len(cases)} cases:")
    for case in cases:
        print(f"Case ID: {case['caseId']}")
        print(f"Subject: {case['subject']}")
        print(f"Status: {case['status']}")
        print(f"Opened by: {case['submittedBy']}")
        print(f"Opened on: {case['timeCreated']}")
        print("-" * 50)
else:
    print("No open cases found.")









from fastapi import FastAPI
import boto3
from botocore.exceptions import ClientError

app = FastAPI()

# Initialize AWS Boto3 client
elbv2_client = boto3.client('elbv2')

@app.get("/unattached-target-groups")
def get_unattached_target_groups():
    try:
        # List all target groups
        target_groups = elbv2_client.describe_target_groups()['TargetGroups']
    except ClientError as e:
        # Handle AWS client errors
        return {"error": f"Failed to describe target groups: {str(e)}"}

    unattached_target_groups = []
    
    # Loop through each target group
    for tg in target_groups:
        tg_arn = tg['TargetGroupArn']
        
        try:
            # Check if the target group has any targets registered
            targets = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)['TargetHealthDescriptions']
            
            # If no targets are registered, add to unattached_target_groups list
            if not targets:
                unattached_target_groups.append(tg_arn)
        
        except ClientError as e:
            # Handle specific target group not found error or any other client errors
            error_code = e.response['Error']['Code']
            if error_code == 'TargetGroupNotFound':
                print(f"Target Group not found: {tg_arn}, continuing to next target group...")
            else:
                print(f"Unexpected error occurred: {str(e)}")
            continue  # Continue the loop to process next target group

    result = []

    # Find the tags for each unattached target group
    for tg_arn in unattached_target_groups:
        try:
            # Get tags for the target group
            tags_response = elbv2_client.describe_tags(ResourceArns=[tg_arn])
            tags = tags_response['TagDescriptions'][0]['Tags']
            
            # Extract the owner and user ID from the tags
            owner = next((tag['Value'] for tag in tags if tag['Key'] == 'Owner'), 'Unknown')
            user = next((tag['Value'] for tag in tags if tag['Key'] == 'User'), 'Unknown')
            
            result.append({"TargetGroupArn": tg_arn, "Owner": owner, "User": user})
        
        except ClientError as e:
            # Handle errors in fetching tags
            print(f"Error fetching tags for {tg_arn}: {str(e)}")
            result.append({"TargetGroupArn": tg_arn, "Owner": "Unknown", "User": "Unknown"})
    
    return result
