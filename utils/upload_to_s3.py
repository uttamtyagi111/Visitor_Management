import boto3
from django.conf import settings


s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

def upload_to_s3(file_obj, filename):
    """
    Uploads a file object to S3 and returns the URL.
    """
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_client.upload_fileobj(file_obj, bucket_name, filename, ExtraArgs={'ACL': 'public-read'})
    url = f"https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{filename}"
    return url



def delete_from_s3(file_url):
    """Delete a file from S3 by its URL."""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # Extract file path from URL
        file_key = file_url.split(f"{bucket_name}/")[-1]
        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        print(f"🗑️ Deleted old file from S3: {file_key}")
    except Exception as e:
        print(f"⚠️ Failed to delete old file from S3: {str(e)}")

