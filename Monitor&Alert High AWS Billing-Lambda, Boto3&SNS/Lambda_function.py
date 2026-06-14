import datetime
import os
import boto3

# Configurations - Hardcode or set up as Lambda Environment Variables
THRESHOLD = float(os.environ.get("BILLING_THRESHOLD", 50.0))
SNS_TOPIC_ARN = os.environ.get(
    "SNS_TOPIC_ARN", "arn:aws:sns:eu-north-1:831963379095:AWS-Billing-Alerts"
)


def lambda_handler(event, context):
    # 1. Initialize boto3 clients (CloudWatch must be forced to us-east-1)
    cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
    sns = boto3.client("sns")

    # Set up time range to scan metrics over the past 24 hours
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(days=1)

    print(
        f"Logging: Scanning metrics between {start_time} and {end_time}..."
    )

    try:
        # 2. Retrieve AWS billing metric from CloudWatch
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/Billing",
            MetricName="EstimatedCharges",
            Dimensions=[{"Name": "Currency", "Value": "USD"}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 24 hours in seconds
            Statistics=["Maximum"],
        )

        datapoints = response.get("Datapoints", [])

        # Gracefully log if no data points are published yet
        if not datapoints:
            print(
                "Logging: No billing datapoints found. (Check if billing preferences are enabled on the root account)."
            )
            return {
                "statusCode": 200,
                "body": "Executed successfully, but no data available.",
            }

        # Extract the highest charge recorded in the 24-hour cycle
        current_billing = datapoints[0]["Maximum"]
        print(f"Logging: Current AWS Billing is at ${current_billing:.2f} USD")
        print(f"Logging: Target limit threshold is ${THRESHOLD:.2f} USD")

        # 3. Compare the billing amount with the threshold
        if current_billing > THRESHOLD:
            print("Logging: Threshold exceeded! Compiling notification...")

            alert_message = (
                f"⚠️ CRITICAL BILLING ALERT ⚠️\n\n"
                f"Your AWS account spend has reached ${current_billing:.2f} USD.\n"
                f"This exceeds your preset alert threshold of ${THRESHOLD:.2f} USD.\n\n"
                f"Please review your AWS Console Cost Explorer to analyze active resources."
            )

            # 4. If billing exceeds threshold, send SNS notification
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="ALERT: AWS Billing Limit Exceeded",
                Message=alert_message,
            )

            print("Logging: Alert notification pushed out via SNS.")
            return {"statusCode": 200, "body": "Alert successfully issued."}

        else:
            # 5. Print logging message if charges are under the budget limit
            print("Logging: Budget parameters stable. Balance within limits.")
            return {"statusCode": 200, "body": "Spend within safe limits."}

    except Exception as e:
        print(f"Logging: Script execution critical failure: {str(e)}")
        raise e
