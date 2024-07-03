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
