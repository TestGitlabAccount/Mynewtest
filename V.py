import boto3

def get_volumes_by_vsad():
    client = boto3.client('ec2')
    
    # Using pagination to handle large datasets
    paginator = client.get_paginator('describe_volumes')
    response_iterator = paginator.paginate()

    vsad_data = {}

    for page in response_iterator:
        volumes = page['Volumes']
        
        for volume in volumes:
            volume_id = volume['VolumeId']
            size = volume['Size']
            state = volume['State']
            
            # Initialize tags
            vsad = None
            born_date = None
            user_id = None
            owner = None
            
            # Parse the tags if they exist
            if 'Tags' in volume:
                tags = {tag['Key']: tag['Value'] for tag in volume['Tags']}
                vsad = tags.get('VSAD')
                born_date = tags.get('BornDate')
                user_id = tags.get('UserID')
                owner = tags.get('Owner')
            
            # Group the volume details by VSAD
            if vsad:
                if vsad not in vsad_data:
                    vsad_data[vsad] = []
                
                vsad_data[vsad].append({
                    'VolumeID': volume_id,
                    'VSAD': vsad,
                    'BornDate': born_date,
                    'UserID': user_id,
                    'Owner': owner,
                    'Size': size,
                    'VolumeState': state
                })

    return vsad_data
