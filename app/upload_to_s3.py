import boto3
import uuid
import hashlib
import time
import os
from config import Config

def create_s3_client():
    return boto3.client("s3", region_name=Config.AWS_REGION)

def generate_unique_filename(original_filename):
    """Generate a unique file name using UUID, timestamp, and a hash of the original filename."""
    # Get the file extension
    file_extension = os.path.splitext(original_filename)[1]
    
    # Generate UUID
    unique_id = uuid.uuid4()
    
    # Get the current timestamp
    timestamp = int(time.time())
    
    # Hash the original filename
    file_hash = hashlib.sha256(original_filename.encode()).hexdigest()[:10]
    
    # Combine them to create a unique filename
    unique_filename = f"{unique_id}_{timestamp}_{file_hash}{file_extension}"
    return unique_filename

def upload_to_s3(file, bucket_name):
    """Uploads a file to the specified S3 bucket with a unique name and returns the URL."""
    try:
        # Generate a unique file name
        original_filename = file.filename
        unique_filename = generate_unique_filename(original_filename)

        # Initialize S3 client and upload the file
        s3 = create_s3_client()
        s3.upload_fileobj(file, bucket_name, unique_filename)

        # Construct and return the URL of the uploaded file
        return f"https://{bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(f"Error uploading to S3: {e}", flush=True)
        return None

