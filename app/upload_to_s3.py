import boto3

def create_s3_client(aws_access_key_id, aws_secret_access_key, aws_region):
    return boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )

def upload_to_s3(file, bucket_name, object_name, aws_access_key_id, aws_secret_access_key, aws_region):
    try:
        s3 = create_s3_client(aws_access_key_id, aws_secret_access_key, aws_region)
        s3.upload_fileobj(file, bucket_name, object_name)
        return f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

