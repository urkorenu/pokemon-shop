import boto3
from botocore.exceptions import ClientError


# Set up the SES client
def send_email(subject, body, recipient, sender="orders@pika-card.store"):
    ses = boto3.client("ses", region_name="eu-north-1")  # Change to your SES region
    try:
        response = ses.send_email(
            Source=sender,
            Destination={
                "ToAddresses": [recipient],
            },
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": body},
                },
            },
        )
        print("Email sent! Message ID:", response["MessageId"])
    except ClientError as e:
        print("Error sending email:", e.response["Error"]["Message"])
