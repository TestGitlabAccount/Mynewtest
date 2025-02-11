I recently worked on automating heap dump generation and analysis. Previously, we used an ActionEngine to collect New Relic data, generate heap dumps, and take necessary actions. However, this process had an 8–10-minute delay, during which significant issues could occur.

To address this, we implemented a pre-stop hook script. The script monitors a specified heap dump path, uploads the generated heap dump to an S3 bucket, and triggers the MatAnalyzer tool for further analysis. The solution introduces two parameters: heap dump path and heap dump location. These parameters ensure the heap dump is created at a defined location, enabling the pre-stop hook to handle it before the pod is terminated.


Subject: Migration to BG-IAS Roles for EC2 and Other Services

Dear Team,

We have identified an IAM role that includes “EC2” in its name, which is not associated with any stack. As a result, it has been marked as an isolated role.

Since this role is isolated, we do not have control over updating it. To address this, we have created a new set of roles. Moving forward, we request the team to start using the BG-IAS role for EC2 creation, as the existing EC2 role may not be appropriate for future use and could be deleted at any time.

For other services, please ensure you use the relevant attached roles accordingly.

Additionally, please share this information with any relevant stakeholders who may need to be informed.

Thank you for your cooperation.


We tested this approach on a test pod, and it has performed successfully so far. After thorough validation, we plan to present it in a demo.
