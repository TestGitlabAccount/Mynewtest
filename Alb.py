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
