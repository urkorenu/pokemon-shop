import boto3
from botocore.exceptions import ClientError

def send_email(subject, body, recipient, sender="orders@pika-card.store"):
    """
    Send an email using AWS SES.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        recipient (str): The recipient's email address.
        sender (str, optional): The sender's email address. Defaults to "orders@pika-card.store".

    Returns:
        None
    """
    ses = boto3.client("ses", region_name="eu-north-1")
    try:
        response = ses.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": f"{body}\nBest regards,\nThe Pika-Card Team"}},
            },
        )
        print("Email sent! Message ID:", response["MessageId"])
    except ClientError as e:
        print("Error sending email:", e.response["Error"]["Message"])