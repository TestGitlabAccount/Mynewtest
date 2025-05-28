import boto3
from botocore.exceptions import ClientError, BotoCoreError


import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_target_groups_with_many_ports(region_name: str, port_threshold: int = 5):
    elbv2 = boto3.client('elbv2', region_name=region_name)

    paginator = elbv2.get_paginator('describe_target_groups')
    response_iterator = paginator.paginate()

    all_target_groups = []

    for page in response_iterator:
        for tg in page['TargetGroups']:
            if tg.get('TargetType') == 'instance':
                all_target_groups.append({
                    'TargetGroupArn': tg['TargetGroupArn'],
                    'TargetGroupName': tg['TargetGroupName']
                })

    results = []

    def process_target_group(tg):
        tg_arn = tg['TargetGroupArn']
        tg_name = tg['TargetGroupName']
        try:
            health_response = elbv2.describe_target_health(TargetGroupArn=tg_arn)
            instance_ports_map = {}

            for description in health_response['TargetHealthDescriptions']:
                target = description['Target']
                instance_id = target.get('Id')
                port = target.get('Port')

                if instance_id not in instance_ports_map:
                    instance_ports_map[instance_id] = set()
                instance_ports_map[instance_id].add(port)

            group_results = []
            for instance_id, ports in instance_ports_map.items():
                if len(ports) >= port_threshold:
                    group_results.append({
                        "target_group_name": tg_name,
                        "region": region_name,
                        "instance_id": instance_id,
                        "num_ports": len(ports),
                        "ports": sorted(list(ports))
                    })
            return group_results
        except Exception as e:
            # Optionally log the error
            return []

    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_tg = {executor.submit(process_target_group, tg): tg for tg in all_target_groups}
        for future in as_completed(future_to_tg):
            result = future.result()
            if result:
                results.extend(result)

    return results












import boto3

def get_target_groups_with_many_ports(region_name: str, port_threshold: int = 5):
    elbv2 = boto3.client('elbv2', region_name=region_name)
    ec2 = boto3.client('ec2', region_name=region_name)

    paginator = elbv2.get_paginator('describe_target_groups')
    response_iterator = paginator.paginate()

    results = []

    for page in response_iterator:
        for tg in page['TargetGroups']:
            tg_arn = tg['TargetGroupArn']
            tg_name = tg['TargetGroupName']
            target_type = tg.get('TargetType')

            if target_type != 'instance':
                continue

            health_response = elbv2.describe_target_health(TargetGroupArn=tg_arn)

            instance_ports_map = {}
            for description in health_response['TargetHealthDescriptions']:
                target = description['Target']
                instance_id = target.get('Id')
                port = target.get('Port')

                if instance_id not in instance_ports_map:
                    instance_ports_map[instance_id] = set()
                instance_ports_map[instance_id].add(port)

            for instance_id, ports in instance_ports_map.items():
                if len(ports) >= port_threshold:
                    results.append({
                        "target_group_name": tg_name,
                        "region": region_name,
                        "instance_id": instance_id,
                        "num_ports": len(ports),
                        "ports": sorted(list(ports))
                    })

    return results







from fastapi import FastAPI, Query
from typing import List
from aws_elb import get_target_groups_with_many_ports

app = FastAPI()

@app.get("/target-groups", summary="Get target groups with >=5 ports per instance")
def list_target_groups(
    region: str = Query(..., description="AWS region name"),
    port_threshold: int = Query(5, ge=1, description="Minimum number of ports to filter by")
) -> List[dict]:
    """
    Returns a list of target groups with instance-type targets that have 5 or more ports.
    """
    try:
        results = get_target_groups_with_many_ports(region, port_threshold)
        return results
    except Exception as e:
        return {"error": str(e)}










def delete_ebs_volumes(volume_ids: list):
    ec2 = boto3.client('ec2')
    results = {}

    for vol_id in volume_ids:
        try:
            ec2.delete_volume(VolumeId=vol_id)
            results[vol_id] = {"status": "success", "message": "Volume deleted successfully"}
        except ClientError as e:
            results[vol_id] = {
                "status": "failed",
                "message": e.response['Error']['Message'],
                "code": e.response['Error']['Code']
            }
        except BotoCoreError as e:
            results[vol_id] = {
                "status": "failed",
                "message": str(e),
                "code": "BotoCoreError"
            }
        except Exception as e:
            results[vol_id] = {
                "status": "failed",
                "message": str(e),
                "code": "UnknownError"
            }
    return results

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from aws.aws_methods import delete_ebs_volumes

app = FastAPI()

class VolumeDeleteRequest(BaseModel):
    volume_ids: List[str]

@app.post("/delete_volumes")
def delete_volumes(request: VolumeDeleteRequest):
    if not request.volume_ids:
        raise HTTPException(status_code=400, detail="No volume IDs provided")
    
    try:
        result = delete_ebs_volumes(request.volume_ids)
        return {
            "requested_volumes": request.volume_ids,
            "results": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")





ess_days()

# Initialize our results JSON structure.
tpm_data = {
    "Clustername": CLUSTER_NAME,
    "Region": REGION,
    "Namespace": NAMESPACE,
    "Services": []
}

services = list_namespace_deployments(NAMESPACE)

# Loop through each service.
for service in services:
    daily_tpm_values = []
    logging.info("Processing service: %s", service)
    
    # For each past day, query New Relic for TPM using business hours in EST.
    for day in past_days:
        utc_start, utc_end = convert_est_to_utc_business_hours(day)
        if utc_start is None or utc_end is None:
            logging.error("Skipping day %s for service %s due to conversion error.", day, service)
            continue

        query = f"""
        {{
          actor {{
            account(id: {ACCOUNT_ID}) {{
              nrql(query: "SELECT rate(count(*), 1 minute) AS tpm FROM Transaction WHERE appName = '{NAMESPACE}-{service}-prod-{REGION}' SINCE '{utc_start}' UNTIL '{utc_end}'") {{
                results
              }}
            }}
          }}
        }}
        """
        try:
            response = requests.post(
                "https://api.newrelic.com/graphql",
                headers={
                    "Content-Type": "application/json",
                    "API-Key": API_KEY
                },
                json={"query": query},
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            logging.error("Request failed for service %s on day %s: %s", service, day, e)
            continue

        try:
            result = response.json()
        except Exception as e:
            logging.error("Error decoding JSON response for service %s on day %s: %s", service, day, e)
            continue

        try:
            results_data = result["data"]["actor"]["account"]["nrql"]["results"]
            if results_data and "tpm" in results_data[0]:
                tpm_value = results_data[0]["tpm"]
                daily_tpm_values.append(tpm_value)
                logging.info("Day %s for service %s: TPM = %s", day, service, tpm_value)
            else:
                logging.warning("No TPM data found for service %s on day %s", service, day)
        except KeyError as e:
            logging.error("Unexpected response structure for service %s on day %s: %s", service, day, e)

    # Compute the 90th percentile for the collected daily TPM values.
    if daily_tpm_values:
        try:
            percentile_90 = int(np.percentile(daily_tpm_values, 90))
        except Exception as e:
            logging.error("Error computing 90th percentile for service %s: %s", service, e)
            percentile_90 = 0
    else:
        percentile_90 = 0

    # Append the result for this service.
    tpm_data["Services"].append({"ServiceName": service, "TPM": percentile_90})
    logging.info("Service %s - 90th Percentile TPM: %s", service, percentile_90)

# Output final JSON result.
print(json.dumps(tpm_data, indent=4))





import requests
import json
import datetime
import numpy as np  # To calculate 90th percentile

API_KEY = "YOUR_NEW_RELIC_API_KEY"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
CLUSTER_NAME = "abc"
REGION = "east"
NAMESPACE = "xyz"

# Function to get past 4 business days (excluding weekends)
def get_past_business_days(days=4):
    dates = []
    today = datetime.date.today()
    while len(dates) < days:
        today -= datetime.timedelta(days=1)
        if today.weekday() < 5:  # Monday to Friday only
            dates.append(today.strftime("%Y-%m-%d"))
    return dates

# Fetch list of deployments
def list_namespace_deployments(namespace):
    return ["service1", "service2", "service3"]  # Replace with actual deployment fetching logic

# Get past 4 business days
past_days = get_past_business_days()

# Store results
tpm_data = {
    "Clustername": CLUSTER_NAME,
    "Region": REGION,
    "Namespace": NAMESPACE,
    "Services": []
}

services = list_namespace_deployments(NAMESPACE)

for service in services:
    daily_tpm_values = []

    for day in past_days:
        query = f"""
        {{
          actor {{
            account(id: {ACCOUNT_ID}) {{
              nrql(query: "SELECT count(*) / 60 AS tpm FROM Transaction WHERE appName = '{NAMESPACE}-{service}-prod-{REGION}' AND hourOf(timestamp) >= 9 AND hourOf(timestamp) <= 20 SINCE '{day} 00:00:00' UNTIL '{day} 23:59:59'") {{
                results
              }}
            }}
          }}
        }}
        """

        response = requests.post(
            "https://api.newrelic.com/graphql",
            headers={"Content-Type": "application/json", "API-Key": API_KEY},
            json={"query": query},
        )

        result = response.json()
        tpm_value = result["data"]["actor"]["account"]["nrql"]["results"][0]["tpm"]
        daily_tpm_values.append(tpm_value)

    # Compute 90th percentile of the collected daily values
    percentile_90 = int(np.percentile(daily_tpm_values, 90))

    # Append to JSON output
    tpm_data["Services"].append({"ServiceName": service, "TPM": percentile_90})

# Print final JSON output
print(json.dumps(tpm_data, indent=4))
