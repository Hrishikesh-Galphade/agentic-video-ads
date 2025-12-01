import time
from io import BytesIO
from urllib.parse import urlparse
import requests # Required for ElevenLabs
from minio import Minio
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions

from .celery_app import celery
from .core.config import settings
from elevenlabs.client import ElevenLabs 


# --- INITIALIZE CLIENTS ---
try:
    # Using your hardcoded endpoint preference
    minio_client = Minio(
        "objectstorage:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )
    print("✅ MinIO client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize MinIO client: {e}")
    minio_client = None

try:
    veo_client = genai.Client(http_options={"api_version": "v1beta"}, api_key=settings.GOOGLE_API_KEY)
    print("✅ Veo client initialized successfully.")
except Exception as e:
    print(f"❌ Failed to initialize Veo client: {e}")
    veo_client = None

video_config = types.GenerateVideosConfig(
    aspect_ratio="16:9", number_of_videos=1, duration_seconds=6, person_generation="ALLOW_ALL")

# --- VIDEO TASK (Existing) ---
@celery.task(name="generate_asset_task", bind=True, autoretry_for=(google_exceptions.ResourceExhausted,), retry_backoff=5, max_retries=5)
def generate_asset_task(self, scene_number: int, visual_description: str) -> dict:
    print(f"🎬 Starting VEO generation for scene {scene_number}")
    
    if not veo_client or not minio_client:
        return {"scene_number": scene_number, "error": "Clients not initialized"}

    try:
        # 1. Generate Video
        operation = veo_client.models.generate_videos(model="veo-2.0-generate-001", prompt=visual_description, config=video_config)
        while not operation.done:
            time.sleep(20)
            operation = veo_client.operations.get(operation)
        
        if not operation.result or not operation.result.generated_videos:
            raise ValueError("No videos generated")
            
        # 2. Download & Upload
        video_bytes = veo_client.files.download(file=operation.result.generated_videos[0].video)
        file_name = f"scene_{scene_number}.mp4"
        
        if not minio_client.bucket_exists(settings.S3_BUCKET_NAME):
            minio_client.make_bucket(settings.S3_BUCKET_NAME)

        minio_client.put_object(
            bucket_name=settings.S3_BUCKET_NAME,
            object_name=file_name,
            data=BytesIO(video_bytes),
            length=len(video_bytes),
            content_type='video/mp4'
        )
        
        asset_url = f"http://localhost:9000/{settings.S3_BUCKET_NAME}/{file_name}"
        return {"scene_number": scene_number, "asset_url": asset_url}

    except google_exceptions.ResourceExhausted as e:
        print(f"RATE LIMIT HIT for scene {scene_number}. Retrying...")
        raise e
    except Exception as e:
        return {"scene_number": scene_number, "error": str(e)}

@celery.task(name="generate_audio_task")
def generate_audio_task(script_text: str) -> dict:
    """
    Generates AI Voiceover using the official ElevenLabs SDK and uploads to MinIO.
    """
    print(f"🎙️ Generating ElevenLabs Audio for: '{script_text[:30]}...'")
    
    if not minio_client:
        return {"error": "MinIO client not initialized"}
    
    # Check for API Key
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        print("❌ ElevenLabs API Key missing in settings.")
        return {"error": "ELEVENLABS_API_KEY is missing"}

    try:
        print("*********************************************")
        print(api_key)
        print("*********************************************")
        # 1. Initialize ElevenLabs Client
        client = ElevenLabs(api_key=api_key)

        # 2. Generate Audio
        # The 'convert' method returns a Generator[bytes], not the bytes directly.
        # We do NOT use 'play()'. We capture the data.
        voice_id = getattr(settings, "ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb") # Default to a known voice if missing
        
        audio_generator = client.text_to_speech.convert(
            text=script_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # 3. Consume the generator to get the full audio file in memory
        audio_bytes = b"".join(audio_generator)
        
        file_name = "voiceover.mp3"

        # 4. Upload to MinIO
        print(f"Uploading '{file_name}' ({len(audio_bytes)} bytes) to MinIO...")
        
        # Create bucket if not exists (safety check)
        if not minio_client.bucket_exists(settings.S3_BUCKET_NAME):
            minio_client.make_bucket(settings.S3_BUCKET_NAME)

        minio_client.put_object(
            bucket_name=settings.S3_BUCKET_NAME,
            object_name=file_name,
            data=BytesIO(audio_bytes),
            length=len(audio_bytes),
            content_type='audio/mpeg'
        )
        
        asset_url = f"http://localhost:9000/{settings.S3_BUCKET_NAME}/{file_name}"
        print(f"✅ Voiceover uploaded: {asset_url}")
        
        return {"type": "audio", "asset_url": asset_url}

    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        # If it's an API key error, this will print the details from the SDK
        return {"error": str(e)}