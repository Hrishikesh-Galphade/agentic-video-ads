# services/orchestrator-agent/src/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from .workflow.graph import graph_app

# Create an instance of the FastAPI application
app = FastAPI(
    title="Generative Video Orchestrator",
    description="The central service for managing the video generation workflow.",
    version="1.0.0"
)

# Pydantic model to define the structure of the request body for creating a job
class JobRequest(BaseModel):
    prompt: str

@app.get("/", tags=["Status"])
def health_check():
    """
    Checks if the service is running and responsive.
    """
    return {"status": "ok", "message": "Orchestrator is running"}

# This is our new endpoint for starting a video generation job
@app.post("/jobs", tags=["Jobs"])
def create_job(request: JobRequest):
    """
    Accepts a prompt and starts the video generation workflow.
    """
    print(f"🚀 Received new job request with prompt: '{request.prompt}'")
    
    # The initial state for our graph
    initial_state = {"prompt": request.prompt}
    
    # Invoke the LangGraph workflow. This will run the entire process
    # from the creative planner to post-production, based on our graph definition.
    final_state = graph_app.invoke(initial_state)
    
    print(f"✅ Workflow finished. Final video URL: {final_state.get('final_video_url')}")
    
    # Return the final state of the workflow
    return final_state