import datetime
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    # Target configuration
    BUCKET_NAME = "your-bucket-name-here"  # Replace with your bucket name
    DAYS_THRESHOLD = 30
    
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Calculate cutoff time (timezone-aware to match S3 UTC format)
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_date = now - datetime.timedelta(days=DAYS_THRESHOLD)
    
    print(f"Starting cleanup for bucket: {BUCKET_NAME}")
    print(f"Deleting objects older than: {cutoff_date}")
    
    deleted_count = 0
    paginator = s3_client.get_paginator('list_objects_v2')
    
    try:
        # Use paginator to handle buckets with more than 1,000 objects
        for page in paginator.paginate(Bucket=BUCKET_NAME):
            if 'Contents' not in page:
                print("No objects found in the bucket.")
                return {"statusCode": 200, "body": "Bucket is empty."}
            
            for obj in page['Contents']:
                object_key = obj['Key']
                object_date = obj['LastModified']
                
                # Check if object age exceeds the threshold
                if object_date < cutoff_date:
                    print(f"Deleting: {object_key} (Modified: {object_date})")
                    
                    s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_key)
                    deleted_count += 1
                    
        print(f"Cleanup complete. Total objects deleted: {deleted_count}")
        return {
            "statusCode": 200,
            "body": f"Successfully deleted {deleted_count} objects."
        }
        
    except ClientError as e:
        print(f"AWS Error: {e.response['Error']['Message']}")
        return {
            "statusCode": 500,
            "body": f"Error executing cleanup: {str(e)}"
        }