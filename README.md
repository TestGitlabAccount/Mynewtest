I recently worked on automating heap dump generation and analysis. Previously, we used an ActionEngine to collect New Relic data, generate heap dumps, and take necessary actions. However, this process had an 8–10-minute delay, during which significant issues could occur.

To address this, we implemented a pre-stop hook script. The script monitors a specified heap dump path, uploads the generated heap dump to an S3 bucket, and triggers the MatAnalyzer tool for further analysis. The solution introduces two parameters: heap dump path and heap dump location. These parameters ensure the heap dump is created at a defined location, enabling the pre-stop hook to handle it before the pod is terminated.

We tested this approach on a test pod, and it has performed successfully so far. After thorough validation, we plan to present it in a demo.
