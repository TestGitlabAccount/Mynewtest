import boto3
from botocore.exceptions import ClientError

def get_unattached_eks_target_groups():
    # Initialize AWS Boto3 client
    elbv2_client = boto3.client('elbv2')

    paginator = elbv2_client.get_paginator('describe_target_groups')
    
    unattached_eks_target_groups = []

    # Paginate through all target groups
    try:
        for page in paginator.paginate():
            target_groups = page['TargetGroups']

            # Loop through each target group
            for tg in target_groups:
                tg_arn = tg['TargetGroupArn']
                tg_name = tg['TargetGroupName']
                
                # Check if the target group is related to EKS
                if "eks" in tg_name.lower():
                    try:
                        # Check if the target group has any targets registered
                        targets = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)['TargetHealthDescriptions']

                        # If no targets are registered, add to unattached_target_groups list
                        if not targets:
                            unattached_eks_target_groups.append(tg_arn)

                    except ClientError as e:
                        # Handle specific target group not found error or any other client errors
                        error_code = e.response['Error']['Code']
                        if error_code == 'TargetGroupNotFound':
                            print(f"Target Group not found: {tg_arn}, continuing to next target group...")
                        else:
                            print(f"Unexpected error occurred while checking target health: {str(e)}")
                        continue  # Continue the loop to process the next target group
    except ClientError as e:
        print(f"Failed to describe target groups: {str(e)}")
        return []

    result = []

    # Find the tags for each unattached target group
    for tg_arn in unattached_eks_target_groups:
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

def write_results_to_file(results, filename="unattached_eks_target_groups.txt"):
    with open(filename, 'w') as file:
        for entry in results:
            tg_arn = entry['TargetGroupArn']
            owner = entry['Owner']
            user = entry['User']
            file.write(f"TargetGroupArn: {tg_arn}, Owner: {owner}, User: {user}\n")

def main():
    unattached_eks_target_groups = get_unattached_eks_target_groups()
    write_results_to_file(unattached_eks_target_groups)
    print("Results have been written to unattached_eks_target_groups.txt")

if __name__ == "__main__":
    main()
