import boto3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    # 1. Initialize Boto3 EC2 client
    ec2 = boto3.client('ec2')
    
    try:
        # 2. Retrieve the instance ID from the event payload
        # Supports EventBridge shapes and direct manual test events
        instance_id = event.get('detail', {}).get('instance-id') or event.get('instance-id')
        
        if not instance_id:
            raise ValueError("Instance ID missing from the event payload.")
            
        # Format the current date (YYYY-MM-DD)
        current_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # 3. Tag the new instance with two tags
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[
                {
                    'Key': 'LaunchDate',
                    'Value': current_date
                },
                {
                    'Key': 'Automated',
                    'Value': 'True'
                }
            ]
        )
        
        # 4. Print confirmation message for logging
        logger.info(f"Successfully tagged instance {instance_id} on {current_date}")
        return {
            'statusCode': 200,
            'body': f"Successfully tagged {instance_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to tag instance: {str(e)}")
        raise e