import requests
import json
import base64
import logging
import os

logger = logging.getLogger(__name__)

OLLAMA_HOST = "http://localhost:11434"
VISION_MODEL = "llama3.2-vision:11b"
TEXT_MODEL = "llama3:8b"

class OllamaService:
    def __init__(self):
        pass

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def analyze_image(self, image_path, user_prompt=None):
        """
        Analyzes an image using llama3.2-vision.
        """
        try:
            base64_image = self._encode_image(image_path)
            
            # Context-aware prompt to categorize and extract data
            system_instruction = """
            You are a fitness AI. Analyze the image.
            1. If FOOD: Identify items, estimate weight, calories, protein, carbs, fat.
            2. If WORKOUT: Identify exercise, equipment, form, estimated calories burned.
            3. If DATA/SCREENSHOT: Extract numbers (weight, steps, etc).
            
            Return JSON ONLY:
            {
                "type": "meal" | "workout" | "metric" | "unknown",
                "summary": "Short description for user",
                "data": {
                    "food_name": "...", "calories": 0, "protein": 0, ... (for meals)
                    "exercise_name": "...", "sets": 0, ... (for workouts)
                    "weight_kg": 0, ... (for metrics)
                }
            }
            """
            
            prompt = f"{system_instruction}\nUser Note: {user_prompt if user_prompt else ''}"

            payload = {
                "model": VISION_MODEL,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
                "format": "json" 
            }

            response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            
            return json.loads(result['response'])

        except Exception as e:
            logger.error(f"Ollama Vision Error: {e}")
            return None

    async def chat(self, prompt, context_data=""):
        """
        Generates a text response using llama3:8b with database context.
        """
        try:
            full_prompt = f"""
            System: You are a helpful fitness coach.
            Context: {context_data}
            
            User: {prompt}
            
            Response (Keep it concise, friendly, and data-driven):
            """
            
            payload = {
                "model": TEXT_MODEL,
                "prompt": full_prompt,
                "stream": False
            }

            response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()['response']

        except Exception as e:
            logger.error(f"Ollama Chat Error: {e}")
            return "My brain is offline properly. Check my connection!"
