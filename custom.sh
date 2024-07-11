#!/bin/bash

# Function to get the count of resources
get_resource_count() {
    resource=$1
    region=$2
    case $resource in
        s3)
            count=$(aws s3api list-buckets --query 'Buckets[*].Name' --output text --region "$region" | wc -w)
            ;;
        rds)
            count=$(aws rds describe-db-instances --query 'DBInstances[*].DBInstanceIdentifier' --output text --region "$region" | wc -w)
            ;;
        eks)
            count=$(aws eks list-clusters --query 'clusters[*]' --output text --region "$region" | wc -w)
            ;;
        ec2)
            count=$(aws ec2 describe-instances --query 'Reservations[*].Instances[*].InstanceId' --output text --region "$region" | wc -w)
            ;;
        msk)
            count=$(aws kafka list-clusters --query 'ClusterInfoList[*].ClusterName' --output text --region "$region" | wc -w)
            ;;
        *)
            count=0
            ;;
    esac
    echo "$count"
}

# Regions to check
regions=("us-east-1" "us-west-2")

# Resources to check
resources=("s3" "rds" "eks" "ec2" "msk")

# Loop through regions and resources
for region in "${regions[@]}"; do
    echo "Region: $region"
    for resource in "${resources[@]}"; do
        count=$(get_resource_count "$resource" "$region")
        echo "Number of $resource resources: $count"
    done
    echo ""
done




#!/bin/bash

# Function to get the count of resources
get_resource_count() {
    resource=$1
    region=$2
    case $resource in
        s3)
            count=$(aws s3api list-buckets --query 'Buckets[*].Name' --output text --region "$region" | wc -w)
            ;;
        rds-instances)
            count=$(aws rds describe-db-instances --query 'DBInstances[*].DBInstanceIdentifier' --output text --region "$region" | wc -w)
            ;;
        rds-clusters)
            count=$(aws rds describe-db-clusters --query 'DBClusters[*].DBClusterIdentifier' --output text --region "$region" | wc -w)
            ;;
        elasticache-clusters)
            count=$(aws elasticache describe-cache-clusters --query 'CacheClusters[*].CacheClusterId' --output text --region "$region" | wc -w)
            ;;
        eks)
            count=$(aws eks list-clusters --query 'clusters[*]' --output text --region "$region" | wc -w)
            ;;
        ec2)
            count=$(aws ec2 describe-instances --query 'Reservations[*].Instances[*].InstanceId' --output text --region "$region" | wc -w)
            ;;
        msk)
            count=$(aws kafka list-clusters --query 'ClusterInfoList[*].ClusterName' --output text --region "$region" | wc -w)
            ;;
        *)
            count=0
            ;;
    esac
    echo "$count"
}

# Regions to check
regions=("us-east-1" "us-west-2")

# Resources to check
resources=("s3" "rds-instances" "rds-clusters" "elasticache-clusters" "eks" "ec2" "msk")

# Create a CSV file to store the results
output_file="aws_resource_counts.csv"
echo "Region,Resource,Count" > "$output_file"

# Loop through regions and resources
for region in "${regions[@]}"; do
    for resource in "${resources[@]}"; do
        count=$(get_resource_count "$resource" "$region")
        echo "$region,$resource,$count" >> "$output_file"
    done
done

