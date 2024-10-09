import boto3
from botocore.exceptions import ClientError

def check_alb_permissions():
    try:
        elbv2_client = boto3.client('elbv2')
        response = elbv2_client.describe_load_balancers()
        alb_names = [lb['LoadBalancerName'] for lb in response['LoadBalancers']]
        print("ALB Names: ", alb_names)
        return True
    except ClientError as e:
        print(f"Error checking ALB permissions: {e}")
        return False

def check_nlb_permissions():
    try:
        elbv2_client = boto3.client('elbv2')
        response = elbv2_client.describe_load_balancers()
        nlb_names = [lb['LoadBalancerName'] for lb in response['LoadBalancers'] if lb['Type'] == 'network']
        print("NLB Names: ", nlb_names)
        return True
    except ClientError as e:
        print(f"Error checking NLB permissions: {e}")
        return False

def check_ebs_volumes_permissions():
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_volumes()
        volume_ids = [vol['VolumeId'] for vol in response['Volumes']]
        print("EBS Volume IDs: ", volume_ids)
        return True
    except ClientError as e:
        print(f"Error checking EBS Volume permissions: {e}")
        return False

def check_ebs_snapshots_permissions():
    try:
        ec2_client = boto3.client('ec2')
        response = ec2_client.describe_snapshots(OwnerIds=['self'])
        snapshot_ids = [snap['SnapshotId'] for snap in response['Snapshots']]
        print("EBS Snapshot IDs: ", snapshot_ids)
        return True
    except ClientError as e:
        print(f"Error checking EBS Snapshot permissions: {e}")
        return False

def check_boto3_permissions():
    print("Checking ALB permissions:")
    check_alb_permissions()
    
    print("\nChecking NLB permissions:")
    check_nlb_permissions()

    print("\nChecking EBS Volume permissions:")
    check_ebs_volumes_permissions()

    print("\nChecking EBS Snapshot permissions:")
    check_ebs_snapshots_permissions()

if __name__ == "__main__":
    check_boto3_permissions()
