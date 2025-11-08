import subprocess
import tempfile
import time
from io import BytesIO
from urllib.parse import urlparse
from minio import Minio
from .celery_app import celery
from .core.config import settings
import os

# --- INITIALIZE MinIO CLIENT (FINAL CORRECTED VERSION) ---
try:
    # Use urlparse to reliably extract the hostname:port from the full URL
    endpoint_url = urlparse(settings.S3_ENDPOINT_URL)
    
    minio_client = Minio(
         endpoint="objectstorage:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False# This correctly sets secure=False for "http"
    )
    print("✅ MinIO client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize MinIO client: {e}")
    minio_client = None


@celery.task(name="post_production_task")
def post_production_task(asset_urls: dict) -> dict:
    """
    Downloads generated assets from MinIO, edits them together using FFMPEG,
    and uploads the final composed video.
    """
    print(f"✂️ Starting REAL post-production with {len(asset_urls)} assets.")

    if not minio_client:
        error_msg = "MinIO client is not initialized. Cannot proceed."
        print(f"❌ {error_msg}")
        return {"error": error_msg}

    # Create a temporary directory that will be automatically cleaned up
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # --- STEP 1: DOWNLOAD ALL ASSETS FROM MINIO ---
            downloaded_files = []
            # Sort the assets by scene number to ensure they are in the correct order
            sorted_assets = sorted(asset_urls.items())

            for key, url in sorted_assets:
                object_name = url.split('/')[-1] # Extracts "scene_1.mp4" from the URL
                local_path = os.path.join(temp_dir, object_name)
                print(f"Downloading {object_name} to {local_path}...")
                minio_client.fget_object(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_name=object_name,
                    file_path=local_path,
                )
                downloaded_files.append(local_path)

            # --- STEP 2: CREATE A MANIFEST FILE FOR FFMPEG ---
            manifest_path = os.path.join(temp_dir, "mylist.txt")
            with open(manifest_path, 'w') as f:
                for file_path in downloaded_files:
                    f.write(f"file '{file_path}'\n")
            
            print(f"FFmpeg manifest created at {manifest_path}")

            # --- STEP 3: RUN FFMPEG TO CONCATENATE VIDEOS ---
            output_path = os.path.join(temp_dir, "final_advertisement.mp4")
            ffmpeg_command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", manifest_path,
                "-c", "copy", # This is a fast way to combine clips without re-encoding
                output_path
            ]
            
            print(f"Running FFMPEG command: {' '.join(ffmpeg_command)}")
            # Execute the command, raise an error if it fails
            subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
            print("✅ FFMPEG concatenation successful.")

            # --- STEP 4: UPLOAD THE FINAL VIDEO TO MINIO ---
            final_file_name = "final_advertisement.mp4"
            print(f"Uploading final video '{final_file_name}' to MinIO...")
            
            # Get the size of the final video for the upload
            file_stat = os.stat(output_path)
            file_size = file_stat.st_size
            
            with open(output_path, 'rb') as final_video_file:
                minio_client.put_object(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_name=final_file_name,
                    data=final_video_file,
                    length=file_size,
                    content_type='video/mp4'
                )

            final_video_url = f"http://localhost:9000/{settings.S3_BUCKET_NAME}/{final_file_name}"
            print(f"✅ Final video uploaded successfully. URL: {final_video_url}")
            
            return {"final_video_url": final_video_url}

        except Exception as e:
            # If FFMPEG fails, subprocess.run will raise an exception.
            error_msg = f"An error occurred during post-production: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_msg += f"\nFFMPEG STDERR: {e.stderr}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
