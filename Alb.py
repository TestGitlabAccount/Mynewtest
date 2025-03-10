import requests
import json
import datetime
import numpy as np  # For calculating the 90th percentile
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Constants (replace these with your actual values)
API_KEY = "YOUR_NEW_RELIC_API_KEY"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
CLUSTER_NAME = "abc"
REGION = "east"
NAMESPACE = "xyz"

# Function to get the last 4 business days (Monday-Friday only)
def get_past_business_days(days=4):
    try:
        dates = []
        current = datetime.date.today()
        while len(dates) < days:
            current -= datetime.timedelta(days=1)
            if current.weekday() < 5:  # 0=Monday, 6=Sunday
                dates.append(current.strftime("%Y-%m-%d"))
        return dates
    except Exception as e:
        logging.error("Error getting past business days: %s", e)
        return []

# Convert a given EST date’s business hours (9:00 to 20:00 EST) to UTC timestamps.
def convert_est_to_utc_business_hours(date_str):
    try:
        est = pytz.timezone('America/New_York')
        utc = pytz.utc
        # Define business hours in EST for the given date
        est_start = datetime.datetime.strptime(date_str + " 09:00:00", "%Y-%m-%d %H:%M:%S")
        est_end = datetime.datetime.strptime(date_str + " 20:00:00", "%Y-%m-%d %H:%M:%S")
        est_start = est.localize(est_start)
        est_end = est.localize(est_end)
        # Convert to UTC
        utc_start = est_start.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        utc_end = est_end.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return utc_start, utc_end
    except Exception as e:
        logging.error("Error converting EST to UTC for date %s: %s", date_str, e)
        return None, None

# Example function to retrieve the list of deployments.
# Replace this with your actual deployment-fetching logic.
def list_namespace_deployments(namespace):
    try:
        return ["service1", "service2", "service3"]
    except Exception as e:
        logging.error("Error listing deployments for namespace %s: %s", namespace, e)
        return []

# Get the past 4 business days.
past_days = get_past_business_days()

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
