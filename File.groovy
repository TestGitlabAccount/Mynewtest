pipeline {
    agent any

    environment {
        KUBECONFIG = "/path/to/your/kubeconfig" // Set your kubeconfig path
    }

    stages {
        stage('Update JAVA_OPTS') {
            steps {
                script {
                    // Define variables
                    def deploymentName = "your-deployment-name"
                    def namespace = "your-namespace"
                    def configFile = "path/to/config.yaml"

                    // Shell script logic as inline Groovy string
                    def updateJavaOptsScript = """
                    #!/bin/bash

                    DEPLOYMENT_NAME="${deploymentName}"
                    NAMESPACE="${namespace}"
                    CONFIG_FILE="${configFile}"

                    # Read required Java options from the config file
                    read_required_java_opts() {
                      grep -E "^\s*-" "$CONFIG_FILE" | sed 's/-//g' | xargs
                    }

                    # Main logic to update JAVA_OPTS
                    update_java_opts() {
                      REQUIRED_OPTS=\$(read_required_java_opts)

                      # Fetch the current deployment
                      echo "Fetching deployment \$DEPLOYMENT_NAME in namespace \$NAMESPACE..."
                      DEPLOYMENT=\$(kubectl get deployment "\$DEPLOYMENT_NAME" -n "\$NAMESPACE" -o json)

                      # Extract JAVA_OPTS from the JSON
                      CURRENT_OPTS=\$(echo "\$DEPLOYMENT" | jq -r '.spec.template.spec.containers[] | select(.env[]?.name == "JAVA_OPTS").env[] | select(.name == "JAVA_OPTS").value')
                      [ -z "\$CURRENT_OPTS" ] && CURRENT_OPTS=""

                      # Add missing options
                      UPDATED_OPTS="\$CURRENT_OPTS"
                      for OPT in \$REQUIRED_OPTS; do
                        if [[ "\$UPDATED_OPTS" != *"\$OPT"* ]]; then
                          UPDATED_OPTS+=" \$OPT"
                        fi
                      done

                      # If no changes are needed, exit
                      if [ "\$CURRENT_OPTS" == "\$UPDATED_OPTS" ]; then
                        echo "JAVA_OPTS is already up to date."
                        exit 0
                      fi

                      echo "Updating JAVA_OPTS..."
                      # Patch the deployment
                      kubectl patch deployment "\$DEPLOYMENT_NAME" -n "\$NAMESPACE" --type=json -p="
                      [
                        {
                          \\"op\\": \\"replace\\",
                          \\"path\\": \\"/spec/template/spec/containers/0/env\\",
                          \\"value\\": [
                            {
                              \\"name\\": \\"JAVA_OPTS\\",
                              \\"value\\": \\"\$UPDATED_OPTS\\"
                            }
                          ]
                        }
                      ]"

                      echo "Deployment updated successfully!"
                    }

                    update_java_opts
                    """

                    // Run the shell script
                    sh script: updateJavaOptsScript, returnStdout: true
                }
            }
        }
    }
}
