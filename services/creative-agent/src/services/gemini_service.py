# services/creative-agent/src/services/gemini_service.py
import google.generativeai as genai
import json
import re
from ..core.config import settings

# Configure the Gemini client with the API key
genai.configure(api_key=settings.GOOGLE_API_KEY)

# The prompt is the "soul" of the agent. This is a carefully crafted instruction.
# --- UPDATED SYSTEM PROMPT ---
SYSTEM_PROMPT = """
You are an elite Creative Director and Copywriter for high-end video advertisements.
Your task is to take a user's prompt and generate a production-ready creative plan for a 30-second video ad.

You must respond in a strictly valid JSON format with exactly two keys: "script" and "storyboard".

### 1. "script" (Voiceover Text)
- This field must contain **ONLY** the spoken words for the Voiceover.
- **DO NOT** include character names (e.g., "Narrator:"), stage directions (e.g., "[Upbeat music]"), or visual cues in this string.
- The text must be written for the ear: rhythmic, engaging, and emotional.
- Keep the length appropriate for a 30-second ad (approximately 60 to 80 words).

### 2. "storyboard" (Visual Prompts)
- This must be an array of 3 to 5 objects representing scenes.
- Each object must have:
  - "scene_number": (integer)
  - "visual_description": (string) A highly detailed, cinematic prompt optimized for an AI Video Generator (like Google Veo or Sora). 
    - Include details on: Subject, Action, Lighting (e.g., "golden hour", "cinematic lighting"), Camera Angle (e.g., "drone shot", "close up"), and Style (e.g., "4k", "photorealistic", "slow motion").

### Example Output Structure:
{
  "script": "Imagine a world where comfort meets style. This is your new reality.",
  "storyboard": [
    { 
      "scene_number": 1, 
      "visual_description": "Cinematic wide shot of a modern living room bathed in warm sunlight, 4k, photorealistic." 
    }
  ]
}
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
        
        # Send the message to Gemini
        response = model.generate_content(prompt)
        
        # Clean the response text to ensure it's valid JSON
        # Sometimes models wrap output in ```json ... ```
        cleaned_json_string = response.text.strip()
        if cleaned_json_string.startswith("```"):
            cleaned_json_string = re.sub(r"^```json|^```", "", cleaned_json_string).strip()
        if cleaned_json_string.endswith("```"):
            cleaned_json_string = cleaned_json_string[:-3].strip()
            
        creative_plan = json.loads(cleaned_json_string)
        
        print("✅ Creative plan generated successfully.")
        return creative_plan
        
    except Exception as e:
        print(f"❌ Error generating creative plan: {e}")
        # Return a fallback error structure
        return {"error": str(e)}