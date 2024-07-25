Topic: IAC (Infrastructure as Code)

Summary of Contributions:
In the realm of Infrastructure as Code, I took full ownership of several key subprojects. Below are the notable projects I led and developed independently:

Nginx Proxy:

Objective: This project aimed to replace Apigee with Nginx proxy deployments.
Achievements: I fully automated the pipeline for deploying Nginx in any given Kubernetes cluster. This pipeline dynamically generates the nginx.conf file and creates the ingress with a certificate ARN (achieved from Shield APIs). The process allows users to complete the full deployment by providing minimal parameters, significantly saving time and effort.
SSO ForgeRock:

Objective: Deploying Single Sign-On (SSO) in EKS clusters.
Achievements: Previously, each user created and deployed their own manifest files, leading to substantial manual effort and errors. I automated this process, allowing users to pass SSO-related configurations while the backend dynamically generates all manifests and deploys them via Helm charts. I managed the project end-to-end, from design to final implementation. Teams have already begun utilizing this automation.
Nextgen Connectors:

Objective: Streamline the deployment process of connectors.
Achievements: The prior method of deploying connectors involved multiple EKS resources created through separate jobs, requiring extensive human intervention. I proposed and implemented a unified pipeline for all applications under IAC. This approach consolidated multiple configmaps into a single configmap, each holding four dynamically generated files based on user-provided configurations. Deployments now occur through Helm, ensuring proper version control and significantly reducing deployment time and effort.
Elasticache and OpenSearch:

Objective: Centralize the creation of Redis and OpenSearch clusters.
Achievements: I developed a centralized approach for creating clusters using CloudFormation Templates (CFTs) generated dynamically based on minimal user inputs (e.g., VSAD, environment, region, size). This backend generation uses Groovy scripting. Currently, we have enabled the creation of clusters, and we plan to integrate update, upgrade, and delete operations into the SRE portal.
These projects exemplify my dedication to enhancing efficiency, reducing manual efforts, and ensuring seamless deployment processes within the infrastructure domain.



Grafana:

Objective: Automate and maintain the non-production Grafana setup.
Achievements: I have automated the complete non-production Grafana setup and regularly maintain it. This includes handling rehydrations and operations such as creating organizations and users. I manage the non-production Grafana infrastructure independently, addressing any issues that arise.
AVI-to-ALB Migration:

Objective: Assist teams in migrating load balancers from AVI to ALB.
Achievements: I provide continuous support to teams migrating their load balancers from AVI to ALB. Additionally, I offer ongoing support for all IAC projects as needed.
These projects exemplify my dedication to enhancing efficiency, reducing manual efforts, and ensuring seamless deployment processes within the infrastructure domain.



GrafanaOps:

Objective: Manage changes to Grafana dashboards in production.
Achievements: Implemented logic for managing changes with a staging area that mirrors production, allowing users to make changes without affecting the live environment. Proposed a solution for onboarding these items to the SRE portal.
Grafana:

Objective: Automate and maintain the non-production Grafana setup.
Achievements: Automated the complete non-production Grafana setup and regularly maintain it, handling rehydrations and operations such as creating organizations and users. Independently manage the non-production Grafana infrastructure, addressing any issues that arise.
AVI-to-ALB Migration:

Objective: Assist teams in migrating load balancers from AVI to ALB.
Achievements: Provide continuous support to teams migrating their load balancers from AVI to ALB. Offer ongoing support for all IAC projects as needed.
Documentation:

Objective: Maintain comprehensive documentation.
Achievements: Maintain documentation in OneConfluence for all tasks related to IAC.
Guardian Project:

K8's Configmap Incorrect Entries:

Achievements: Implemented logic across all environments and created a cron job to execute and generate weekly reports.
IBM MO Standards:

Achievements: Developed logic to extract both IBM MO and MO product level standards using Ansible Playbooks.
VSAD's MQ Data:

Achievements: Onboarded several VSAD's MQ data to Guardian and managed rehydrations for unreachable servers.
Adhoc Jobs:

Achievements: Provided various adhoc jobs including Kubernetes Node Health Check, Adhoc K8's NodeCount report, Xtables check, and leveraging EKS Dumps job.
Additional Contributions:

K2view Application Infra Support (VSAD: GA5V):

Achievements: Delivered automation jobs for creating ENIs, EC2s, and EFS, and mounting EFS to EC2s. Provide constant support as needed.
Dast Scan Infra Support (VSAD: JNSV):

Achievements: Offer consistent infrastructure support for the Dast Scans process. Manage rehydrations as the application is not yet onboarded to Nebula.
Infra Support (VSAD: 121V):

Achievements: Manage the creation of EC2 instances for installing the Catchpoint application and provide rehydration support. Offer infrastructure support for non-production Grafana, including handling unreachable conditions, managing user and organization configurations, and other related responsibilities. Also handle rehydration tasks as the application is not yet onboarded to Nebula.
These projects demonstrate my commitment to:

Improving efficiency
Reducing manual effort
Ensuring smooth deployment processes





EC2 Instances

aws ec2 describe-instances --region us-east-1 --query "Reservations[*].Instances[*].[InstanceId]" --output text --no-paginate | wc -l

RDS Instances

aws rds describe-db-instances --region us-east-1 --query "DBInstances[*].DBInstanceIdentifier" --output text --no-paginate | wc -l

EKS Clusters

aws eks list-clusters --region us-east-1 --query "clusters" --output text --no-paginate | wc -l

ElastiCache Clusters

aws elasticache describe-cache-clusters --region us-east-1 --query "CacheClusters[*].CacheClusterId" --output text --no-paginate | wc -l

S3 Buckets

Note: S3 buckets are global resources and are not limited to a specific region. However, you can count the total number of buckets in your account:

aws s3api list-buckets --query "Buckets[*].Name" --output text | wc -l

OpenSearch Domains

aws opensearch list-domain-names --region us-east-1 --query "DomainNames[*].DomainName" --output text --no-paginate | wc -l

These commands will provide you with the count of each resource type in the specified region.













Deploying GitLab Runners on EKS Using Helm and values.yaml
Table of Contents
Introduction
Prerequisites
Setting Up EKS Cluster
Installing Helm
Configuring values.yaml
Deploying GitLab Runners
Monitoring and Logging
Scaling Runners
Troubleshooting
Conclusion
References
Introduction
This document provides a step-by-step guide on deploying GitLab Runners on an Amazon EKS (Elastic Kubernetes Service) cluster using Helm and a custom values.yaml file. By deploying GitLab Runners as Kubernetes pods, you can leverage the scalability and orchestration capabilities of Kubernetes to handle CI/CD workloads efficiently.

Prerequisites
Before proceeding with the deployment, ensure you have the following prerequisites in place:

AWS Account: Access to an AWS account with permissions to create EKS clusters and other resources.
AWS CLI: Installed and configured on your local machine.
kubectl: Installed for managing the Kubernetes cluster.
Helm: Installed for deploying applications on Kubernetes.
GitLab Account: Access to your GitLab instance where you will register the runners.
IAM Role: An IAM role with sufficient permissions to manage the EKS cluster and nodes.
Setting Up EKS Cluster
Create an EKS Cluster:

Use the AWS Management Console or AWS CLI to create a new EKS cluster. Here’s an example using the AWS CLI:

bash
Copy code
aws eks create-cluster \
    --name my-gitlab-runner-cluster \
    --role-arn arn:aws:iam::<account-id>:role/EKS-ClusterRole \
    --resources-vpc-config subnetIds=subnet-abc123,securityGroupIds=sg-abc123
Configure kubectl for EKS:

Update your Kubernetes configuration to interact with the EKS cluster:

bash
Copy code
aws eks update-kubeconfig --region <region> --name my-gitlab-runner-cluster
Verify the Cluster:

Ensure your kubectl is configured correctly:

bash
Copy code
kubectl get nodes
Installing Helm
Add the Helm Repository:

Add the official GitLab Helm repository to your Helm setup:

bash
Copy code
helm repo add gitlab https://charts.gitlab.io
helm repo update
Verify Helm Installation:

Check if Helm is installed correctly:

bash
Copy code
helm version
Configuring values.yaml
The values.yaml file is crucial for configuring GitLab Runners. Below is a sample configuration with explanations for each parameter.

yaml
Copy code
# values.yaml

gitlabUrl: https://gitlab.com/
runnerRegistrationToken: "<your-registration-token>"
runners:
  config: |
    [[runners]]
      name = "my-runner"
      executor = "kubernetes"
      [runners.kubernetes]
        image = "alpine:latest"
        namespace = "gitlab-runners"
        poll_timeout = 180
        [runners.kubernetes.pod_security_context]
          run_as_user = 1000
          run_as_group = 3000
          fs_group = 2000
  replicas: 2
  imagePullSecrets:
    - name: my-registry-secret
  namespace: gitlab-runners
Key Parameters
gitlabUrl: The URL of your GitLab instance.
runnerRegistrationToken: The token used for registering runners with GitLab. Obtain this from your GitLab project or group settings.
runners: Configurations specific to the GitLab Runner.
executor: The executor type; set to kubernetes for this deployment.
namespace: The Kubernetes namespace where runners will be deployed.
imagePullSecrets: Secrets for pulling Docker images if needed.
Deploying GitLab Runners
Create Namespace:

First, create the namespace for the GitLab Runners:

bash
Copy code
kubectl create namespace gitlab-runners
Deploy with Helm:

Use Helm to deploy the GitLab Runner chart with the customized values.yaml:

bash
Copy code
helm upgrade --install gitlab-runner -f values.yaml gitlab/gitlab-runner --namespace gitlab-runners
Verify Deployment:

Check the status of your GitLab Runners deployment:

bash
Copy code
kubectl get pods --namespace gitlab-runners
Ensure the pods are running without errors.

Monitoring and Logging
Access Runner Logs:

You can view logs for a specific runner pod using:

bash
Copy code
kubectl logs <pod-name> --namespace gitlab-runners
Prometheus Metrics:

If Prometheus is enabled, access runner metrics at /metrics endpoint of the GitLab Runner pod.

Scaling Runners
You can scale the number of GitLab Runner pods by updating the replicas field in the values.yaml file.

yaml
Copy code
runners:
  replicas: 5
Apply the changes using Helm:

bash
Copy code
helm upgrade --install gitlab-runner -f values.yaml gitlab/gitlab-runner --namespace gitlab-runners
Troubleshooting
Here are some common issues and troubleshooting steps:

Pods Stuck in Pending State:

Check if there are sufficient resources in your EKS cluster.
Verify that the values.yaml file is correctly configured.
Image Pull Errors:

Ensure Docker registry secrets are correctly configured.
Registration Failures:

Double-check the runnerRegistrationToken.
Ensure network connectivity to the GitLab instance.
Conclusion
Deploying GitLab Runners on an EKS cluster provides a robust and scalable CI/CD solution. By following the steps outlined in this document, you can efficiently manage and scale GitLab Runners to meet your organization's needs.

References
GitLab Runner Documentation
Helm Documentation
AWS EKS Documentation
This documentation should provide a clear and comprehensive guide for deploying GitLab Runners on EKS using Helm. Feel free to customize the document further to suit specific organizational requirements or add any additional information pertinent to your setup.
