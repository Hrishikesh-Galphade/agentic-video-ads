# services/orchestrator-agent/src/workflow/nodes.py
# FINAL VERSION - With explicit queue routing for Celery tasks

import requests
from celery import group
from .state import VideoGenerationState
from ..core.config import settings
from .celery_client import celery_app

# --- NODE 1: LIVE (No changes here) ---
def creative_planner_node(state: VideoGenerationState) -> dict:
    print("--- 🧠 NODE: Creative Planner (Live) ---")
    prompt = state.get("prompt")
    try:
        response = requests.post(settings.CREATIVE_AGENT_URL, json={"prompt": prompt}, timeout=120)
        response.raise_for_status()
        creative_plan = response.json()
        print("✅ Creative plan received from agent.")
        return {"script": creative_plan.get("script"), "storyboard": creative_plan.get("storyboard")}
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to call Creative Director service: {e}")
        return {"error_message": f"Creative Director service failed: {e}"}

# --- NODE 2: UPGRADED WITH QUEUE ROUTING ---
def asset_generator_node(state: VideoGenerationState) -> dict:
    """
    Dispatches tasks to asset generator workers and handles the results robustly.
    """
    print("\n--- 🎬 NODE: Asset Generator (Live via Celery) ---")
    if state.get("error_message"): return {}

    storyboard = state.get("storyboard")
    
    asset_tasks = group(
        celery_app.signature(
            "generate_asset_task", 
            args=[scene['scene_number'], scene.get('visual_description', '')],
            queue='asset_queue' 
        )
        for scene in storyboard
    )
    
    print(f"Dispatching {len(storyboard)} asset generation tasks to the 'asset_queue'...")
    result_group = asset_tasks.apply_async()
    
    print("Waiting for asset generation to complete...")
    results = result_group.get(timeout=600)
    
    # --- NEW, ROBUST RESULT HANDLING ---
    asset_urls = {}
    errors = []
    # Sort results by scene number to maintain order
    sorted_results = sorted(results, key=lambda x: x.get('scene_number', 0))

    for res in sorted_results:
        if "error" in res and res["error"] is not None:
            # If a worker returned an error, log it and add it to our list
            error_message = f"Scene {res.get('scene_number', 'unknown')} failed: {res['error']}"
            print(f"❌ Worker Error: {error_message}")
            errors.append(error_message)
        elif "asset_url" in res:
            # If the worker succeeded, add the URL to our dictionary
            asset_urls[f"scene_{res['scene_number']}_video"] = res['asset_url']

    # If any errors occurred, we stop the workflow by setting the error message in the state
    if errors:
        return {"error_message": "One or more asset generation tasks failed: " + " | ".join(errors)}
    
    print(f"✅ All assets generated successfully. URLs: {asset_urls}")
    
    return {"asset_urls": asset_urls}
# --- NODE 3: UPGRADED WITH QUEUE ROUTING ---
def post_production_node(state: VideoGenerationState) -> dict:
    print("\n--- ✂️ NODE: Post-Production (Live via Celery) ---")
    if state.get("error_message"): return {}
    
    asset_urls = state.get("asset_urls")
    
    print("Dispatching post-production task to the 'post_production_queue'...")
    # Send the task and specify the destination queue
    task = celery_app.send_task(
        "post_production_task", 
        args=[asset_urls], 
        # --- THE FIX IS HERE ---
        queue='post_production_queue'
    )
    
    print("Waiting for post-production to complete...")
    result = task.get(timeout=300)
    
    print(f"✅ Post-production finished.")
    return {"final_video_url": result.get("final_video_url")}