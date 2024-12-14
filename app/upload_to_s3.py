import boto3
import uuid
import hashlib
import time
import os
from PIL import Image, ImageOps
from io import BytesIO
from config import Config

def create_s3_client():
    """
    Create an S3 client using the AWS region specified in the configuration.

    Returns:
        boto3.client: The S3 client.
    """
    return boto3.client("s3", region_name=Config.AWS_REGION)

def generate_unique_filename(original_filename):
    """
    Generate a unique file name using UUID, timestamp, and a hash of the original filename.

    Args:
        original_filename (str): The original file name.

    Returns:
        str: The generated unique file name.
    """
    file_extension = os.path.splitext(original_filename)[1]
    unique_id = uuid.uuid4()
    timestamp = int(time.time())
    file_hash = hashlib.sha256(original_filename.encode()).hexdigest()[:10]
    return f"{unique_id}_{timestamp}_{file_hash}{file_extension}"

def optimize_image(file, max_width=1200, quality=85):
    """
    Optimize the image to reduce its size while maintaining quality.

    Args:
        file (file-like object): The image file to optimize.
        max_width (int, optional): The maximum width of the image. Defaults to 1200.
        quality (int, optional): The quality of the optimized image. Defaults to 85.

    Returns:
        BytesIO: The optimized image file.
    """
    try:
        img = Image.open(file)
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        if img.width > max_width:
            aspect_ratio = img.height / img.width
            img = img.resize((max_width, int(max_width * aspect_ratio)), Image.Resampling.LANCZOS)
        optimized_image = BytesIO()
        img.save(optimized_image, format="JPEG", optimize=True, quality=quality)
        optimized_image.seek(0)
        return optimized_image
    except Exception as e:
        print(f"Error optimizing image: {e}", flush=True)
        return None

def upload_to_s3(file, bucket_name):
    """
    Upload an optimized file to the specified S3 bucket with a unique name and return the URL.

    Args:
        file (file-like object): The file to upload.
        bucket_name (str): The name of the S3 bucket.

    Returns:
        str: The URL of the uploaded file, or None if the upload failed.
    """
    try:
        unique_filename = generate_unique_filename(file.filename)
        optimized_file = optimize_image(file)
        if not optimized_file:
            return None
        s3 = create_s3_client()
        s3.upload_fileobj(optimized_file, bucket_name, unique_filename)
        return f"https://{bucket_name}.s3.{Config.AWS_REGION}.amazonaws.com/{unique_filename}"
    except Exception as e:
        print(f"Error uploading to S3: {e}", flush=True)
        return None