import subprocess
import tempfile
import os
import random
from io import BytesIO
from urllib.parse import urlparse
from minio import Minio
from .celery_app import celery
from .core.config import settings

# --- INITIALIZE CLIENT ---
try:
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

@celery.task(name="post_production_task")
def post_production_task(asset_urls: dict) -> dict:
    print(f"✂️ Starting post-production with {len(asset_urls)} assets.")

    if not minio_client:
        return {"error": "MinIO client not initialized"}

    # --- 1. SELECT RANDOM BACKGROUND MUSIC ---
    # Assumes files exist in /app/assets/music (copied via Dockerfile)
    music_dir = "/app/assets/music"
    bg_music_path = None
    try:
        if os.path.exists(music_dir):
            music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            if music_files:
                selected_music = random.choice(music_files)
                bg_music_path = os.path.join(music_dir, selected_music)
                print(f"🎵 Selected background music: {selected_music}")
            else:
                print("⚠️ No music files found.")
    except Exception as e:
        print(f"⚠️ Error selecting music: {e}")

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            downloaded_videos = []
            voiceover_path = None
            
            # --- 2. DOWNLOAD ASSETS ---
            for key, url in asset_urls.items():
                object_name = url.split('/')[-1]
                local_path = os.path.join(temp_dir, object_name)
                
                print(f"Downloading {object_name}...")
                minio_client.fget_object(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_name=object_name,
                    file_path=local_path,
                )

                # Identify if this is the voiceover audio
                if key == "voiceover_audio":
                    voiceover_path = local_path
                else:
                    downloaded_videos.append(local_path)

            # Sort videos by scene number (keys usually 'scene_1', 'scene_2'...)
            downloaded_videos.sort()

            # --- 3. CONCATENATE VIDEOS (Create visual track) ---
            manifest_path = os.path.join(temp_dir, "mylist.txt")
            with open(manifest_path, 'w') as f:
                for file_path in downloaded_videos:
                    f.write(f"file '{file_path}'\n")
            
            silent_video_path = os.path.join(temp_dir, "silent_combined.mp4")
            subprocess.run([
                "ffmpeg", "-f", "concat", "-safe", "0", "-i", manifest_path, 
                "-c", "copy", silent_video_path
            ], check=True, capture_output=True)

            # --- 4. MIX AUDIO AND VIDEO ---
            final_output_path = os.path.join(temp_dir, "final_advertisement.mp4")
            
            # Base command: Input 0 is Video
            ffmpeg_cmd = ["ffmpeg", "-i", silent_video_path]
            
            if voiceover_path and bg_music_path:
                print("Merging: Video + Voiceover + Background Music")
                # Input 1: Voice, Input 2: Music
                ffmpeg_cmd.extend(["-i", voiceover_path, "-i", bg_music_path])
                
                # Filter Logic:
                # [2:a]volume=0.1[bg] -> Lower music volume to 10%
                # [1:a][bg]amix...    -> Mix Voice and lowered Music
                # -map 0:v -> Use video from Input 0
                # -map [aout] -> Use mixed audio
                # -shortest -> Cut music when video ends
                ffmpeg_cmd.extend([
                    "-filter_complex", "[2:a]volume=0.1[bg];[1:a][bg]amix=inputs=2:duration=first[aout]",
                    "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-shortest",
                    final_output_path
                ])
                
            elif voiceover_path:
                print("Merging: Video + Voiceover")
                ffmpeg_cmd.extend(["-i", voiceover_path])
                ffmpeg_cmd.extend([
                    "-c:v", "copy", "-c:a", "aac", "-map", "0:v", "-map", "1:a", "-shortest", final_output_path
                ])
            else:
                print("Merging: Video Only")
                os.rename(silent_video_path, final_output_path)
                ffmpeg_cmd = None

            if ffmpeg_cmd:
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # --- 5. UPLOAD FINAL VIDEO ---
            final_file_name = "final_advertisement.mp4"
            file_stat = os.stat(final_output_path)
            
            with open(final_output_path, 'rb') as f:
                minio_client.put_object(
                    bucket_name=settings.S3_BUCKET_NAME,
                    object_name=final_file_name,
                    data=f,
                    length=file_stat.st_size,
                    content_type='video/mp4'
                )

            final_url = f"http://localhost:9000/{settings.S3_BUCKET_NAME}/{final_file_name}"
            print(f"✅ Final video uploaded: {final_url}")
            
            return {"final_video_url": final_url}

        except Exception as e:
            print(f"❌ Post-production error: {e}")
            return {"error": str(e)}