# services/creative-agent/src/services/gemini_service.py
import google.generativeai as genai
import json
from ..core.config import settings

# Configure the Gemini client with the API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

# The prompt is the "soul" of the agent. This is a carefully crafted instruction.
SYSTEM_PROMPT = """
You are an expert Creative Director for a modern advertising agency.
Your task is to take a user's prompt and generate a creative plan for a 30-second video ad.

You must respond in a valid JSON format with two keys: "script" and "storyboard".

- The "script" should be a short, punchy, and compelling voiceover script for the ad.
- The "storyboard" should be an array of JSON objects. Each object represents a scene and must have two keys: "scene_number" (an integer) and "visual_description" (a detailed description of the visuals for that scene, which will be used to generate video clips).

Generate 3 scenes for the storyboard. Be creative and professional.
"""

# Initialize the Generative Model
model = genai.GenerativeModel(
    model_name="gemini-flash-latest", # Using flash for speed and cost-effectiveness
    system_instruction=SYSTEM_PROMPT
)

def generate_creative_plan(prompt: str) -> dict:
    """
    Takes a user prompt and generates a script and storyboard using the Gemini model.
    """
    try:
        print(f"🧠 Generating creative plan for prompt: '{prompt}'")
        response = model.generate_content(prompt)
        
        # The response text should be a JSON string. We need to parse it.
        # A good practice is to clean up the response in case the model adds backticks
        cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        creative_plan = json.loads(cleaned_json_string)
        print("✅ Creative plan generated successfully.")
        return creative_plan
    except Exception as e:
        print(f"❌ Error generating creative plan: {e}")
        # In a real app, you'd have more robust error handling
        return {"error": str(e)}