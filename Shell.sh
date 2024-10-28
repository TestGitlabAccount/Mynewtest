#!/bin/bash

# Jenkins credentials
JENKINS_URL="http://your-jenkins-url"
USER="your-username"
API_TOKEN="your-api-token"
LABEL="your-label-to-check"

# Get all nodes (computers) associated with the specified label
nodes=$(curl -s -u "$USER:$API_TOKEN" "$JENKINS_URL/label/$LABEL/api/json?pretty=true")

# Loop through each node that matches the given label
for node_name in $(echo "$nodes" | jq -r '.nodes[].displayName'); do
    # Get the node's offline status
    is_offline=$(curl -s -u "$USER:$API_TOKEN" "$JENKINS_URL/computer/$node_name/api/json" | jq -r '.offline')

    if [[ "$is_offline" == "true" ]]; then
        echo "Node $node_name is offline. Removing label $LABEL."
        
        # Get current labels and remove the specified label
        current_labels=$(curl -s -u "$USER:$API_TOKEN" "$JENKINS_URL/computer/$node_name/config.xml" | grep "<label>" | sed 's/<\/\?label>//g')
        
        # Remove the label from the list (if present)
        updated_labels=$(echo "$current_labels" | sed "s/$LABEL//g")
        
        # Update the node config with new labels
        curl -X POST -u "$USER:$API_TOKEN" \
             -H "Content-Type: application/xml" \
             --data-binary "<slave><label>$updated_labels</label></slave>" \
             "$JENKINS_URL/computer/$node_name/config.xml"

        echo "Updated labels for $node_name: $updated_labels"
    else
        echo "Node $node_name is online. No action needed."
    fi
done
