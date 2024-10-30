import boto3
from datetime import datetime

def get_lambda_data_by_vsad():
    lambda_client = boto3.client('lambda')
    cloudwatch_client = boto3.client('cloudwatch')
    tag_client = boto3.client('resourcegroupstaggingapi')
    
    vsad_data = {}
    
    # Get the list of all Lambda functions
    paginator = lambda_client.get_paginator('list_functions')
    response_iterator = paginator.paginate()
    
    for page in response_iterator:
        for function in page['Functions']:
            function_name = function['FunctionName']
            creation_date = function['LastModified']  # Function creation date
            arn = function['FunctionArn']
            
            # Initialize variables for tags
            vsad = None
            owner = None
            user_id = None
            
            # Get tags for the Lambda function
            tag_response = lambda_client.list_tags(Resource=arn)
            if 'Tags' in tag_response:
                tags = tag_response['Tags']
                vsad = tags.get('VSAD')
                owner = tags.get('Owner')
                user_id = tags.get('UserID')

            # Get the last invocation time (if available)
            try:
                invocations = cloudwatch_client.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                    StartTime=datetime.utcnow() - timedelta(days=30),
                    EndTime=datetime.utcnow(),
                    Period=3600,
                    Statistics=['Sum']
                )
                last_invocation = max([datapoint['Timestamp'] for datapoint in invocations['Datapoints']]) if invocations['Datapoints'] else None
            except Exception as e:
                last_invocation = None  # No invocations found
            
            # Group Lambda details by VSAD
            if vsad:
                if vsad not in vsad_data:
                    vsad_data[vsad] = []
                
                vsad_data[vsad].append({
                    'LambdaName': function_name,
                    'CreationDate': creation_date,
                    'LastInvocatedAt': last_invocation,
                    'VSAD': vsad,
                    'Owner': owner,
                    'UserID': user_id
                })
    
    return vsad_data
