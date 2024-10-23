import boto3

def find_and_delete_disconnected_load_balancers():
    elb_client = boto3.client('elbv2')
    load_balancers = elb_client.describe_load_balancers()['LoadBalancers']
    
    disconnected_load_balancers = []
    deleted_load_balancers_report = []

    for lb in load_balancers:
        lb_arn = lb['LoadBalancerArn']
        target_groups = elb_client.describe_target_groups(LoadBalancerArn=lb_arn)['TargetGroups']

        if not target_groups:
            print(f"Load balancer {lb['LoadBalancerName']} is not connected to any target groups.")
            disconnected_load_balancers.append(lb)

            # Deleting the load balancer
            elb_client.delete_load_balancer(LoadBalancerArn=lb_arn)
            deleted_load_balancers_report.append(lb['LoadBalancerName'])
            print(f"Deleted load balancer {lb['LoadBalancerName']}.")

    # Reporting the deleted load balancers
    if deleted_load_balancers_report:
        print("\nDeleted Load Balancers Report:")
        for lb_name in deleted_load_balancers_report:
            print(lb_name)
    else:
        print("No load balancers were deleted.")

if __name__ == "__main__":
    find_and_delete_disconnected_load_balancers()






import boto3

def find_and_delete_disconnected_target_groups():
    elb_client = boto3.client('elbv2')
    target_groups = elb_client.describe_target_groups()['TargetGroups']
    
    disconnected_target_groups = []
    deleted_target_groups_report = []

    for tg in target_groups:
        tg_arn = tg['TargetGroupArn']
        lb_arn_list = elb_client.describe_listeners()['Listeners']

        # Check if the target group is attached to any load balancer listeners
        attached_to_lb = False
        for listener in lb_arn_list:
            if tg_arn in [tg['TargetGroupArn'] for tg in elb_client.describe_rules(ListenerArn=listener['ListenerArn'])['Rules']]:
                attached_to_lb = True
                break
        
        if not attached_to_lb:
            print(f"Target group {tg['TargetGroupName']} is not attached to any load balancers.")
            disconnected_target_groups.append(tg)

            # Deleting the target group
            elb_client.delete_target_group(TargetGroupArn=tg_arn)
            deleted_target_groups_report.append(tg['TargetGroupName'])
            print(f"Deleted target group {tg['TargetGroupName']}.")

    # Reporting the deleted target groups
    if deleted_target_groups_report:
        print("\nDeleted Target Groups Report:")
        for tg_name in deleted_target_groups_report:
            print(tg_name)
    else:
        print("No target groups were deleted.")

if __name__ == "__main__":
    find_and_delete_disconnected_target_groups()











from fastapi import FastAPI
import boto3

app = FastAPI()

# Initialize Boto3 clients
elb_client = boto3.client('elbv2')


# Endpoint to find and delete load balancers not connected to any target groups
@app.get("/cleanup/load-balancers")
def find_and_delete_disconnected_load_balancers():
    load_balancers = elb_client.describe_load_balancers()['LoadBalancers']
    
    disconnected_load_balancers = []
    deleted_load_balancers_report = []

    for lb in load_balancers:
        lb_arn = lb['LoadBalancerArn']
        target_groups = elb_client.describe_target_groups(LoadBalancerArn=lb_arn)['TargetGroups']

        if not target_groups:
            disconnected_load_balancers.append(lb['LoadBalancerName'])

            # Deleting the load balancer
            elb_client.delete_load_balancer(LoadBalancerArn=lb_arn)
            deleted_load_balancers_report.append(lb['LoadBalancerName'])

    return {
        "disconnected_load_balancers": disconnected_load_balancers,
        "deleted_load_balancers_report": deleted_load_balancers_report
    }


# Endpoint to find and delete target groups not attached to any load balancers
@app.get("/cleanup/target-groups")
def find_and_delete_disconnected_target_groups():
    target_groups = elb_client.describe_target_groups()['TargetGroups']
    
    disconnected_target_groups = []
    deleted_target_groups_report = []

    for tg in target_groups:
        tg_arn = tg['TargetGroupArn']
        lb_arn_list = elb_client.describe_listeners()['Listeners']

        attached_to_lb = False
        for listener in lb_arn_list:
            if tg_arn in [tg['TargetGroupArn'] for tg in elb_client.describe_rules(ListenerArn=listener['ListenerArn'])['Rules']]:
                attached_to_lb = True
                break
        
        if not attached_to_lb:
            disconnected_target_groups.append(tg['TargetGroupName'])

            # Deleting the target group
            elb_client.delete_target_group(TargetGroupArn=tg_arn)
            deleted_target_groups_report.append(tg['TargetGroupName'])

    return {
        "disconnected_target_groups": disconnected_target_groups,
        "deleted_target_groups_report": deleted_target_groups_report
    }





from fastapi import FastAPI
import boto3

app = FastAPI()

# Initialize Boto3 EC2 and ELB clients
elb_client = boto3.client('elbv2')
ec2_client = boto3.client('ec2')


# Existing Load Balancer and Target Group cleanup APIs go here ...


# New API to check EC2 volumes' DeleteOnTermination attribute
@app.get("/check-volumes")
def check_and_modify_ec2_volumes():
    instances = ec2_client.describe_instances()['Reservations']
    modified_instances = []

    for reservation in instances:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            block_device_mappings = instance.get('BlockDeviceMappings', [])

            for device in block_device_mappings:
                volume_id = device['Ebs']['VolumeId']
                delete_on_termination = device['Ebs']['DeleteOnTermination']

                # If DeleteOnTermination is set to NO, modify it to YES
                if not delete_on_termination:
                    # Modify the volume to set DeleteOnTermination to YES
                    ec2_client.modify_instance_attribute(
                        InstanceId=instance_id,
                        BlockDeviceMappings=[
                            {
                                'DeviceName': device['DeviceName'],
                                'Ebs': {
                                    'DeleteOnTermination': True
                                }
                            }
                        ]
                    )
                    modified_instances.append(instance_id)

    if modified_instances:
        return {
            "message": "The DeleteOnTermination attribute was modified to YES for the following instances:",
            "modified_instances": modified_instances
        }
    else:
        return {
            "message": "No modifications were necessary. All volumes already had DeleteOnTermination set to YES."
        }







from fastapi import FastAPI
import boto3

app = FastAPI()

# Initialize the AWS ELBv2 client
elbv2_client = boto3.client('elbv2')

# Function to fetch ALBs without Target Groups, categorized by VSAD
def get_albs_without_target_groups():
    unattached_albs_by_vsad = {}

    # Get all ALBs (Application Load Balancers)
    load_balancers = elbv2_client.describe_load_balancers()

    # Iterate through each ALB
    for lb in load_balancers['LoadBalancers']:
        lb_arn = lb['LoadBalancerArn']
        lb_name = lb['LoadBalancerName']

        # Check if there are target groups attached to this ALB
        target_groups = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)

        # If no target groups are attached
        if not target_groups['TargetGroups']:
            # Get ALB tags
            tags = elbv2_client.describe_tags(ResourceArns=[lb_arn])

            # Extract VSAD tag, if present
            vsad_tag = None
            for tag_description in tags['TagDescriptions']:
                for tag in tag_description['Tags']:
                    if tag['Key'] == 'VSAD':
                        vsad_tag = tag['Value']
                        break
            
            # Categorize by VSAD level
            if vsad_tag:
                if vsad_tag not in unattached_albs_by_vsad:
                    unattached_albs_by_vsad[vsad_tag] = []
                unattached_albs_by_vsad[vsad_tag].append({
                    "ALBName": lb_name,
                    "ALBArn": lb_arn
                })

    return unattached_albs_by_vsad





from fastapi import FastAPI
import boto3

app = FastAPI()

# Initialize the AWS ELBv2 client
elbv2_client = boto3.client('elbv2')

# Function to fetch Target Groups without Load Balancers, categorized by VSAD
def get_target_groups_without_lbs():
    unattached_tgs_by_vsad = {}

    # Get all target groups
    target_groups = elbv2_client.describe_target_groups()

    # Iterate through each target group
    for tg in target_groups['TargetGroups']:
        tg_arn = tg['TargetGroupArn']
        tg_name = tg['TargetGroupName']

        # Check if the target group is attached to any load balancers
        lb_arns = tg.get('LoadBalancerArns', [])

        # If no load balancers are attached
        if not lb_arns:
            # Get tags associated with the target group
            tags = elbv2_client.describe_tags(ResourceArns=[tg_arn])

            # Extract VSAD tag, if present
            vsad_tag = None
            for tag_description in tags['TagDescriptions']:
                for tag in tag_description['Tags']:
                    if tag['Key'] == 'VSAD':
                        vsad_tag = tag['Value']
                        break
            
            # Categorize by VSAD level
            if vsad_tag:
                if vsad_tag not in unattached_tgs_by_vsad:
                    unattached_tgs_by_vsad[vsad_tag] = []
                unattached_tgs_by_vsad[vsad_tag].append({
                    "TargetGroupName": tg_name,
                    "TargetGroupArn": tg_arn
                })

    return unattached_tgs_by_vsad

@app.get("/tgs-unattached/")
async def list_tgs_unattached():
    unattached_tgs = get_target_groups_without_lbs()
    return {"unattached_tgs_by_vsad": unattached_tgs}

@app.get("/albs-unattached/")
async def list_albs_unattached():
    unattached_albs = get_albs_without_target_groups()
    return {"unattached_albs_by_vsad": unattached_albs}

