#!/usr/bin/env python3

import boto3
import csv
import time
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError

MAX_WORKERS = 5
RETRY_LIMIT = 5
BATCH_SLEEP_SECONDS = 1  # wait after each batch

def describe_target_health_with_backoff(client, tg_arn):
    retry = 0
    while retry < RETRY_LIMIT:
        try:
            return client.describe_target_health(TargetGroupArn=tg_arn)
        except ClientError as e:
            if e.response['Error']['Code'] == 'Throttling':
                wait = 2 ** retry + random.uniform(0, 1)
                print(f"[WARN] Throttled. Retrying in {wait:.2f}s...")
                time.sleep(wait)
                retry += 1
            else:
                raise e
    raise Exception(f"Max retries exceeded for {tg_arn}")

def get_target_groups(region, prefix_filter=None):
    elbv2 = boto3.client('elbv2', region_name=region)
    paginator = elbv2.get_paginator('describe_target_groups')
    iterator = paginator.paginate()
    
    groups = []
    for page in iterator:
        for tg in page['TargetGroups']:
            if tg.get('TargetType') == 'instance':
                if not prefix_filter or tg['TargetGroupName'].startswith(prefix_filter):
                    groups.append({
                        'TargetGroupArn': tg['TargetGroupArn'],
                        'TargetGroupName': tg['TargetGroupName']
                    })
    return groups

def process_target_group(elbv2, tg, region, port_threshold):
    try:
        health = describe_target_health_with_backoff(elbv2, tg['TargetGroupArn'])
        instance_ports = {}
        for desc in health['TargetHealthDescriptions']:
            target = desc['Target']
            iid = target.get('Id')
            port = target.get('Port')
            instance_ports.setdefault(iid, set()).add(port)

        rows = []
        for iid, ports in instance_ports.items():
            if len(ports) >= port_threshold:
                rows.append({
                    'target_group_name': tg['TargetGroupName'],
                    'region': region,
                    'instance_id': iid,
                    'num_ports': len(ports),
                    'ports': ",".join(map(str, sorted(ports)))
                })
        return rows
    except Exception as e:
        print(f"[ERROR] {tg['TargetGroupName']}: {str(e)}")
        return []

def generate_report(region, output_file, port_threshold=5, prefix_filter=None):
    elbv2 = boto3.client('elbv2', region_name=region)
    target_groups = get_target_groups(region, prefix_filter)
    total = len(target_groups)
    print(f"[INFO] Found {total} target groups. Processing...")

    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['target_group_name', 'region', 'instance_id', 'num_ports', 'ports']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for i, tg in enumerate(target_groups):
                futures.append(executor.submit(process_target_group, elbv2, tg, region, port_threshold))

                # batching: pause every N submissions to avoid bursts
                if i % (MAX_WORKERS * 5) == 0:
                    time.sleep(BATCH_SLEEP_SECONDS)

            for future in as_completed(futures):
                rows = future.result()
                for row in rows:
                    writer.writerow(row)

    print(f"[DONE] Report written to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate ELB target group port report")
    parser.add_argument('--region', required=True, help='AWS region')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--ports', type=int, default=5, help='Minimum number of ports (default: 5)')
    parser.add_argument('--prefix', help='Optional target group name prefix filter')

    args = parser.parse_args()
    generate_report(args.region, args.output, args.ports, args.prefix)

if __name__ == '__main__':
    main()
