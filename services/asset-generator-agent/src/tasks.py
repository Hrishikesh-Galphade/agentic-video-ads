# services/asset-generator-agent/src/tasks.py
# FINAL MERGED VERSION - Incorporates bucket check, corrected endpoint, and rate-limit retries

import time
from io import BytesIO
from urllib.parse import urlparse
from minio import Minio
from google import genai
from google.genai import types
# --- NEW IMPORT for rate limiting ---
from google.api_core import exceptions as google_exceptions

from .celery_app import celery
from .core.config import settings

# --- INITIALIZE MinIO CLIENT ---
# Using the corrected, valid hostname 'minio-storage'
try:
    minio_client = Minio(
        "minio-storage:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    print("✅ MinIO client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize MinIO client: {e}")
    minio_client = None

# --- INITIALIZE VEO CLIENT ---
try:
    veo_client = genai.Client(http_options={"api_version": "v1beta"}, api_key=settings.GOOGLE_API_KEY)
    print("✅ Veo client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Veo client: {e}")
    veo_client = None

# --- DEFINE VEO CONFIGURATION ---
video_config = types.GenerateVideosConfig(
    aspect_ratio="16:9", number_of_videos=1, duration_seconds=6, person_generation="ALLOW_ALL")

# --- UPDATED TASK DECORATOR with retry logic ---
@celery.task(
    name="generate_asset_task",
    bind=True,
    autoretry_for=(google_exceptions.ResourceExhausted,),
    retry_backoff=5,
    retry_jitter=True,
    max_retries=5
)
def generate_asset_task(self, scene_number: int, visual_description: str) -> dict:
    """
    Generates a video clip with Veo and uploads it, with automatic retries for rate limits.
    """
    print(f"🎬 Starting VEO generation for scene {scene_number}: '{visual_description}'")
    
    if not veo_client or not minio_client:
        error_msg = "A required client (Veo or MinIO) is not initialized."
        print(f"❌ {error_msg}")
        return {"scene_number": scene_number, "error": error_msg}
    
    # --- UPDATED try/except block for specific error handling ---
    try:
        # --- VEO Generation (no change) ---
        operation = veo_client.models.generate_videos(model="veo-2.0-generate-001", prompt=visual_description, config=video_config)
        print(f"⏳ Waiting for Veo to generate video for scene {scene_number}...")
        while not operation.done:
            time.sleep(20)
            operation = veo_client.operations.get(operation)
        result = operation.result
        if not result or not result.generated_videos:
            raise ValueError("Veo operation completed but no videos were generated.")
        generated_video_file_handle = result.generated_videos[0].video
        print(f"✅ Video generated successfully: {generated_video_file_handle.uri}")
        
        # --- Download (no change) ---
        print(f"Downloading video data from Google's servers...")
        video_bytes = veo_client.files.download(file=generated_video_file_handle)
        file_name = f"scene_{scene_number}.mp4"
        
        # --- Your bucket check logic (integrated) ---
        bucket_name = settings.S3_BUCKET_NAME
        print(f"Uploading '{file_name}' to MinIO bucket '{bucket_name}'...")
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
            
        # --- Upload (no change) ---
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=BytesIO(video_bytes),
            length=len(video_bytes),
            content_type='video/mp4'
        )
        asset_url = f"http://localhost:9000/{bucket_name}/{file_name}"
        print(f"✅ Upload successful. URL: {asset_url}")
        
        return {"scene_number": scene_number, "asset_url": asset_url}

    except google_exceptions.ResourceExhausted as e:
        # This specific exception means we've hit a rate limit.
        print(f"RATE LIMIT HIT for scene {scene_number}. Celery will retry automatically. Error: {e}")
        # Re-raise the exception so Celery's autoretry_for can catch it.
        raise e
    except Exception as e:
        # For any other type of error, we fail immediately and report it.
        error_msg = f"A non-retriable error occurred for scene {scene_number}: {e}"
        print(f"❌ {error_msg}")
        return {"scene_number": scene_number, "error": error_msg}