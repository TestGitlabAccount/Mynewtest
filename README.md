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
