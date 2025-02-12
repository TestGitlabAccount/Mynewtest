aws cloudwatch get-metric-statistics \
    --namespace "Kafka" \
    --metric-name "cpuidle" \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --period 60 \
    --statistics Average \
    --output json


pipeline {
    agent any

    environment {
        KUBECONFIG = "/path/to/your/kubeconfig" // Replace with your kubeconfig file path
    }

    stages {
        stage('Update JAVA_OPTS') {
            steps {
                script {
                    // Define variables
                    def deploymentName = "your-deployment-name"  // Replace with your deployment name
                    def namespace = "your-namespace"             // Replace with your namespace
                    def configPath = "/path/to/your/kubeconfig"  // Replace with the path to your kubeconfig
                    def requiredOpts = "-XX:+UseParallelOldGC -Xms512m -Xmx1024m -XX:+UseContainerSupport" // Set your required JAVA_OPTS
                    
                    // Shell script logic
                    def updateJavaOptsScript = '''
                    #!/bin/bash

                    DEPLOYMENT_NAME="''' + deploymentName + '''"
                    NAMESPACE="''' + namespace + '''"
                    KUBECONFIG="''' + configPath + '''"
                    REQUIRED_OPTS="''' + requiredOpts + '''"

                    echo "Fetching deployment $DEPLOYMENT_NAME in namespace $NAMESPACE..."

                    # Fetch the deployment JSON
                    DEPLOYMENT=$(kubectl --kubeconfig="$KUBECONFIG" get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o json)
                    if [ $? -ne 0 ]; then
                        echo "Failed to fetch the deployment. Please check the deployment name, namespace, and kubeconfig."
                        exit 1
                    fi

                    # Extract the current JAVA_OPTS
                    CURRENT_OPTS=$(echo "$DEPLOYMENT" | jq -r '.spec.template.spec.containers[] | select(.env[]?.name == "JAVA_OPTS").env[] | select(.name == "JAVA_OPTS").value')
                    [ -z "$CURRENT_OPTS" ] && CURRENT_OPTS=""

                    # Add missing options
                    UPDATED_OPTS="$CURRENT_OPTS"
                    for OPT in $REQUIRED_OPTS; do
                        if [[ "$UPDATED_OPTS" != *"$OPT"* ]]; then
                            UPDATED_OPTS+=" $OPT"
                        fi
                    done

                    # If no changes are needed, exit
                    if [ "$CURRENT_OPTS" == "$UPDATED_OPTS" ]; then
                        echo "JAVA_OPTS is already up to date."
                        exit 0
                    fi

                    echo "Updating JAVA_OPTS..."
                    # Patch the deployment with the updated JAVA_OPTS
                    kubectl --kubeconfig="$KUBECONFIG" patch deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" --type=json -p="
                    [
                        {
                            \\"op\\": \\"replace\\",
                            \\"path\\": \\"/spec/template/spec/containers/0/env\\",
                            \\"value\\": [
                                {
                                    \\"name\\": \\"JAVA_OPTS\\",
                                    \\"value\\": \\"$UPDATED_OPTS\\"
                                }
                            ]
                        }
                    ]"

                    if [ $? -eq 0 ]; then
                        echo "Deployment updated successfully!"
                    else
                        echo "Failed to update the deployment."
                        exit 1
                    fi
                    '''

                    // Execute the shell script
                    sh script: updateJavaOptsScript, returnStdout: true
                }
            }
        }
    }
}





pipeline {
    agent any

    environment {
        KUBECONFIG = "/path/to/your/kubeconfig" // Replace with your kubeconfig file path
    }

    stages {
        stage('Update JAVA_OPTS') {
            steps {
                script {
                    // Define variables
                    def deploymentName = "your-deployment-name"  // Replace with your deployment name
                    def namespace = "your-namespace"             // Replace with your namespace
                    def configPath = "/path/to/your/kubeconfig"  // Replace with the path to your kubeconfig
                    def requiredOpts = "-XX:+UseParallelOldGC -Xms512m -Xmx1024m -XX:+UseContainerSupport" // Set your required JAVA_OPTS
                    
                    // Shell script logic
                    def updateJavaOptsScript = '''
                    #!/bin/bash

                    DEPLOYMENT_NAME="''' + deploymentName + '''"
                    NAMESPACE="''' + namespace + '''"
                    KUBECONFIG="''' + configPath + '''"
                    REQUIRED_OPTS="''' + requiredOpts + '''"

                    echo "Fetching deployment $DEPLOYMENT_NAME in namespace $NAMESPACE..."

                    # Fetch the deployment JSON
                    DEPLOYMENT=$(kubectl --kubeconfig="$KUBECONFIG" get deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" -o json)
                    if [ $? -ne 0 ]; then
                        echo "Failed to fetch the deployment. Please check the deployment name, namespace, and kubeconfig."
                        exit 1
                    fi

                    # Extract the current JAVA_OPTS
                    CURRENT_OPTS=$(echo "$DEPLOYMENT" | jq -r '.spec.template.spec.containers[] | select(.env[]?.name == "JAVA_OPTS").env[] | select(.name == "JAVA_OPTS").value')
                    [ -z "$CURRENT_OPTS" ] && CURRENT_OPTS=""

                    echo "Current JAVA_OPTS: $CURRENT_OPTS"
                    echo "Required JAVA_OPTS: $REQUIRED_OPTS"

                    # Convert REQUIRED_OPTS to an array
                    IFS=' ' read -r -a REQUIRED_ARRAY <<< "$REQUIRED_OPTS"
                    
                    # Add missing options from REQUIRED_OPTS to CURRENT_OPTS
                    UPDATED_OPTS="$CURRENT_OPTS"
                    for OPT in "${REQUIRED_ARRAY[@]}"; do
                        if [[ "$CURRENT_OPTS" != *"$OPT"* ]]; then
                            UPDATED_OPTS+=" $OPT"
                        fi
                    done

                    echo "Updated JAVA_OPTS: $UPDATED_OPTS"

                    # If no changes are needed, exit
                    if [ "$CURRENT_OPTS" == "$UPDATED_OPTS" ]; then
                        echo "JAVA_OPTS is already up to date."
                        exit 0
                    fi

                    echo "Updating JAVA_OPTS..."
                    # Patch the deployment with the updated JAVA_OPTS
                    kubectl --kubeconfig="$KUBECONFIG" patch deployment "$DEPLOYMENT_NAME" -n "$NAMESPACE" --type=json -p="
                    [
                        {
                            \\"op\\": \\"replace\\",
                            \\"path\\": \\"/spec/template/spec/containers/0/env\\",
                            \\"value\\": [
                                {
                                    \\"name\\": \\"JAVA_OPTS\\",
                                    \\"value\\": \\"$UPDATED_OPTS\\"
                                }
                            ]
                        }
                    ]"

                    if [ $? -eq 0 ]; then
                        echo "Deployment updated successfully!"
                    else
                        echo "Failed to update the deployment."
                        exit 1
                    fi
                    '''

                    // Execute the shell script
                    sh script: updateJavaOptsScript, returnStdout: true
                }
            }
        }
    }
}
