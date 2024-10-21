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
