import boto3
import logging

# Set up structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    
    # --- TASK 1: STOP AUTO-STOP INSTANCES ---
    # Find running instances tagged with 'Action: Auto-Stop'
    stop_filters = [
        {'Name': 'tag:Action', 'Values': ['Auto-Stop']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
    
    running_response = ec2.describe_instances(Filters=stop_filters)
    instances_to_stop = [
        instance['InstanceId']
        for reservation in running_response['Reservations']
        for instance in reservation['Instances']
    ]
    
    if instances_to_stop:
        logger.info(f"Targeting instances for stop: {instances_to_stop}")
        ec2.stop_instances(InstanceIds=instances_to_stop)
        logger.info(f"Successfully sent stop request for: {instances_to_stop}")
    else:
        logger.info("Zero running instances found matching tag 'Action: Auto-Stop'.")

    # --- TASK 2: START AUTO-START INSTANCES ---
    # Find stopped instances tagged with 'Action: Auto-Start'
    start_filters = [
        {'Name': 'tag:Action', 'Values': ['Auto-Start']},
        {'Name': 'instance-state-name', 'Values': ['stopped']}
    ]
    
    stopped_response = ec2.describe_instances(Filters=start_filters)
    instances_to_start = [
        instance['InstanceId']
        for reservation in stopped_response['Reservations']
        for instance in reservation['Instances']
    ]
    
    if instances_to_start:
        logger.info(f"Targeting instances for start: {instances_to_start}")
        ec2.start_instances(InstanceIds=instances_to_start)
        logger.info(f"Successfully sent start request for: {instances_to_start}")
    else:
        logger.info("Zero stopped instances found matching tag 'Action: Auto-Start'.")
        
    return {
        'statusCode': 200,
        'body': 'Execution finalized without critical structural errors.'
    }
