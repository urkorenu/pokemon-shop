import boto3
import uuid
import hashlib
import time
import os
from PIL import Image, ImageOps
from io import BytesIO
from config import Config


def create_s3_client():
    return boto3.client("s3", region_name=Config.AWS_REGION)


def generate_unique_filename(original_filename):
    """Generate a unique file name using UUID, timestamp,
    and a hash of the original filename."""
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


def optimize_image(file, max_width=1200, quality=85):
    """
    Optimize the image to reduce its size while maintaining quality.
    - max_width: The maximum width of the image.
    - quality: The image quality (1-100), where 100 is the best quality.
    """
    try:
        # Open the image using Pillow
        img = Image.open(file)

        # Correct orientation using EXIF data (prevents unwanted rotation)
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if the image has an alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize the image if it's larger than max_width
        if img.width > max_width:
            aspect_ratio = img.height / img.width
            new_height = int(max_width * aspect_ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Save the optimized image to a BytesIO object
        optimized_image = BytesIO()
        img.save(optimized_image, format="JPEG", optimize=True, quality=quality)
        optimized_image.seek(0)

        return optimized_image
    except Exception as e:
        print(f"Error optimizing image: {e}", flush=True)
        return None


def upload_to_s3(file, bucket_name):
    """Uploads an optimized file to the specified S3 bucket
    with a unique name and returns the URL."""
    try:
        # Generate a unique file name
        original_filename = file.filename
        unique_filename = generate_unique_filename(original_filename)

        # Optimize the image
        optimized_file = optimize_image(file)
        if not optimized_file:
            return None

        # Initialize S3 client and upload the optimized file
        s3 = create_s3_client()
        s3.upload_fileobj(optimized_file, bucket_name, unique_filename)

        # Construct and return the URL of the uploaded file
        return (
            f"https://{bucket_name}.s3.{Config.AWS_REGION}"
            f".amazonaws.com/{unique_filename}"
        )
    except Exception as e:
        print(f"Error uploading to S3: {e}", flush=True)
        return None
