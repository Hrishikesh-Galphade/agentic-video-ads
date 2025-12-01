# services/orchestrator-agent/src/workflow/nodes.py

import requests
from celery import group
from .state import VideoGenerationState
from ..core.config import settings
from .celery_client import celery_app

# --- NODE 1: CREATIVE PLANNER ---
def creative_planner_node(state: VideoGenerationState) -> dict:
    print("--- 🧠 NODE: Creative Planner (Live) ---")
    prompt = state.get("prompt")
    try:
        response = requests.post(settings.CREATIVE_AGENT_URL, json={"prompt": prompt}, timeout=120)
        response.raise_for_status()
        creative_plan = response.json()
        print("✅ Creative plan received from agent.")
        
        # We return the script explicitly so it updates the state
        return {
            "script": creative_plan.get("script"), 
            "storyboard": creative_plan.get("storyboard")
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to call Creative Director service: {e}")
        return {"error_message": f"Creative Director service failed: {e}"}

# --- NODE 2: ASSET GENERATOR (Updated for Audio) ---
def asset_generator_node(state: VideoGenerationState) -> dict:
    print("\n--- 🎬 NODE: Asset Generator (Live via Celery) ---")
    if state.get("error_message"): return {}

    storyboard = state.get("storyboard")
    script_text = state.get("script", "") # Get the script text
    
    asset_urls = {}
    errors = []

    # 1. Generate Video Assets Sequentially
    print(f"Dispatching {len(storyboard)} video tasks sequentially to 'asset_queue'...")
    
    for scene in storyboard:
        print(f"   > Generating video for Scene {scene['scene_number']}...")
        try:
            # Create signature
            video_task = celery_app.signature(
                "generate_asset_task", 
                args=[scene['scene_number'], scene.get('visual_description', '')],
                queue='asset_queue' 
            )
            # Execute synchronously (wait for result)
            res = video_task.apply_async().get(timeout=300) # 5 min timeout per clip
            
            if res and "error" in res:
                error_message = f"Scene {scene['scene_number']} failed: {res['error']}"
                print(f"❌ {error_message}")
                errors.append(error_message)
            elif res and "asset_url" in res:
                print(f"✅ Scene {scene['scene_number']} generated: {res['asset_url']}")
                asset_urls[f"scene_{res['scene_number']}_video"] = res['asset_url']
                
        except Exception as e:
            error_message = f"Scene {scene['scene_number']} exception: {str(e)}"
            print(f"❌ {error_message}")
            errors.append(error_message)

    # 2. Generate Audio Asset (Sequentially after videos)
    if script_text:
        print(f"   > Generating audio for script...")
        try:
            audio_task = celery_app.signature(
                "generate_audio_task",
                args=[script_text],
                queue='asset_queue'
            )
            res = audio_task.apply_async().get(timeout=120)
            
            if res and "error" in res:
                error_message = f"Audio generation failed: {res['error']}"
                print(f"❌ {error_message}")
                errors.append(error_message)
            elif res and res.get("type") == "audio":
                print(f"✅ Audio generated: {res['asset_url']}")
                asset_urls["voiceover_audio"] = res['asset_url']
                
        except Exception as e:
            error_message = f"Audio generation exception: {str(e)}"
            print(f"❌ {error_message}")
            errors.append(error_message)

    if errors:
        return {"error_message": "Asset generation errors: " + " | ".join(errors)}
    
    print(f"✅ All assets generated. Total files: {len(asset_urls)}")
    return {"asset_urls": asset_urls}

# --- NODE 3: POST PRODUCTION (Unchanged logic, just standard) ---
def post_production_node(state: VideoGenerationState) -> dict:
    print("\n--- ✂️ NODE: Post-Production (Live via Celery) ---")
    if state.get("error_message"): return {}
    
    asset_urls = state.get("asset_urls")
    
    print("Dispatching post-production task...")
    task = celery_app.send_task(
        "post_production_task", 
        args=[asset_urls], 
        queue='post_production_queue'
    )
    
    print("Waiting for post-production to complete...")
    result = task.get(timeout=300)
    
    if result and "error" in result:
         return {"error_message": result["error"]}

    print(f"✅ Post-production finished.")
    return {"final_video_url": result.get("final_video_url")}