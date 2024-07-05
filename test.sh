#!/bin/bash

# Ask for environment selection
echo "Select Environment:"
echo "1. NONPROD"
echo "2. PROD"
read -p "Enter choice [1 or 2]: " env_choice

# Determine role and account based on selection
if [ "$env_choice" -eq 1 ]; then
    role="arn:aws:iam::2345:role/saml-np-eks"
    account="wls-np"
    echo "Selected Environment: NONPROD"
elif [ "$env_choice" -eq 2 ]; then
    role="arn:aws:iam::2345:role/saml-prod-eks"
    account=""
    echo "Selected Environment: PROD"
else
    echo "Invalid selection. Exiting."
    exit 1
fi

# Ask for cluster name
read -p "Enter cluster name: " clustername

# Ask for region
read -p "Enter AWS region: " region

# Set username
username="abshma"

# Determine kubectl command based on environment selection
kubectl_command="kubectl kluster ${clustername} -a ${account} --account --region ${region} -t namespace-admin --role-name ${role} -u ${username}"

# Display the command
echo "Generated kubectl command:"
echo "${kubectl_command}"

# Execute the command
${kubectl_command}
