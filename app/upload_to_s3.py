import boto3
from config import Config


def create_s3_client():
    return boto3.client("s3", region_name=Config.AWS_REGION)


def upload_to_s3(file, bucket_name, object_name):
    """Uploads a file to the specified S3 bucket and returns the URL."""
    try:
        s3 = create_s3_client()
        s3.upload_fileobj(file, bucket_name, object_name)
        return (
            f"https://{bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{object_name}"
        )
    except Exception as e:
        print(f"Error uploading to S3: {e}", flush=True)
        return None
