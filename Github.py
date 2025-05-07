import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# Initialize clients
elbv2_client = boto3.client('elbv2')
cloudwatch_client = boto3.client('cloudwatch')

# Time range - last 1 day
end_time = datetime.utcnow()
start_time = end_time - timedelta(days=1)

# Function to get peak LCU for a single ALB
def get_peak_lcu(lb_arn, lb_name):
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/ApplicationELB',
            MetricName='ConsumedLCUs',
            Dimensions=[{'Name': 'LoadBalancer', 'Value': lb_arn.split('/')[-2] + '/' + lb_arn.split('/')[-1]}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5-minute granularity
            Statistics=['Maximum']
        )
        datapoints = response.get('Datapoints', [])
        if datapoints:
            peak = max(dp['Maximum'] for dp in datapoints)
            return {'LoadBalancerName': lb_name, 'PeakLCU': peak}
        else:
            return {'LoadBalancerName': lb_name, 'PeakLCU': 0}
    except Exception as e:
        return {'LoadBalancerName': lb_name, 'PeakLCU': 'Error', 'Error': str(e)}

# Main function
def fetch_all_peak_lcus():
    results = []

    # Step 1: Get all load balancers
    lbs = []
    paginator = elbv2_client.get_paginator('describe_load_balancers')
    for page in paginator.paginate():
        lbs.extend(page['LoadBalancers'])

    print(f"Found {len(lbs)} load balancers.")

    # Step 2: Use ThreadPoolExecutor for concurrency
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_lb = {
            executor.submit(get_peak_lcu, lb['LoadBalancerArn'], lb['LoadBalancerName']): lb
            for lb in lbs
        }
        for future in as_completed(future_to_lb):
            result = future.result()
            results.append(result)

    # Step 3: Sort and print report
    results.sort(key=lambda x: x.get('PeakLCU', 0), reverse=True)
    for res in results:
        print(f"{res['LoadBalancerName']}: Peak LCU = {res['PeakLCU']}")

    return results

# Run
if __name__ == "__main__":
    report = fetch_all_peak_lcus()
