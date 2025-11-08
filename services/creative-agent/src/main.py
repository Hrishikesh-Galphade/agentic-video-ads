# services/creative-agent/src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .services.gemini_service import generate_creative_plan

app = FastAPI(
    title="Creative Director Agent",
    version="1.0.0"
)

class CreativeRequest(BaseModel):
    prompt: str

@app.get("/", tags=["Status"])
def health_check():
    return {"status": "ok", "message": "Creative Director Agent is running"}

@app.post("/v1/creative-plan", tags=["Creative"])
def create_creative_plan(request: CreativeRequest):
    """
    Receives a prompt and returns a generated script and storyboard.
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    
    plan = generate_creative_plan(request.prompt)

    if "error" in plan:
        raise HTTPException(status_code=500, detail=f"Failed to generate creative plan: {plan['error']}")
    
    return plan