import google.generativeai as genai
import json
import logging
import os
import asyncio
import time
from config import GEMINI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def _generate_with_retry(self, inputs):
        """Helper to run generation with retry logic for rate limits."""
        max_retries = 3
        delay = 60  # Retry delay for rate limits

        for attempt in range(max_retries):
            try:
                # 3-second pacing delay to avoid hitting rate limits
                await asyncio.sleep(3)
                
                response = await asyncio.to_thread(self.model.generate_content, inputs)
                return response
            except Exception as e:
                error_str = str(e)
                # Check for rate limit indicators (429 or Resource Exhausted)
                if "429" in error_str or "Resource" in error_str or "quota" in error_str.lower():
                    logger.warning(f"Rate limit exceeded. Waiting {delay} seconds before retry (Attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Reraise or return None for other errors
                    logger.error(f"Gemini API Error: {e}")
                    return None
        return None

    async def analyze_meal(self, image_path, user_notes=None):
        """
        Analyzes a food image to estimate nutrition.
        """
        prompt = f"""
        Analyze this food image. The user notes are: "{user_notes if user_notes else 'None'}".
        Identify the food items, estimate portions, and provide nutritional info.
        
        Return a valid JSON object with the following structure (do NOT use Markdown code blocks, just raw JSON):
        {{
            "food_items": [
                {{
                    "name": "Food Name",
                    "estimated_weight_g": 100,
                    "calories": 150,
                    "protein_g": 10,
                    "carbs_g": 20,
                    "fats_g": 5
                }}
            ],
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fats": 0,
            "confidence_level": "High/Medium/Low",
            "notes": "Brief summary or observation"
        }}
        """
        
        try:
            sample_file = genai.upload_file(path=image_path, display_name="Meal Image")
            
            # Use the retry helper
            response = await self._generate_with_retry([prompt, sample_file])
            
            if not response:
                return None

            # Clean up JSON response
            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            return json.loads(text_response)
            
        except Exception as e:
            logger.error(f"Error analyzing meal: {e}")
            return None

    async def analyze_workout(self, image_path, user_notes=None):
        """
        Analyzes a workout image (equipment or exercise).
        """
        prompt = f"""
        Analyze this gym/workout photo. User notes: "{user_notes if user_notes else 'None'}".
        Identify the exercise, equipment, assess form (if visible), and estimate calories burned for a typical set.
        
        Return a valid JSON object with the following structure (do NOT use Markdown code blocks, just raw JSON):
        {{
            "exercise_name": "Name of exercise",
            "equipment_used": "Equipment name",
            "sets": 3,
            "reps": 10,
            "estimated_calories_burned": 50,
            "form_feedback": "Observations on form or setup",
            "confidence_level": "High/Medium/Low"
        }}
        """
        
        try:
            sample_file = genai.upload_file(path=image_path, display_name="Workout Image")
            
            response = await self._generate_with_retry([prompt, sample_file])
            
            if not response:
                return None

             # Clean up JSON response
            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            return json.loads(text_response)

        except Exception as e:
            logger.error(f"Error analyzing workout: {e}")
            return None

    async def analyze_health_app_screenshot(self, image_path):
        """
        Analyzes a screenshot of a health/fitness app to extract body metrics.
        """
        prompt = """
        Analyze this screenshot from a health/fitness app.
        Extract any visible body metrics such as Weight, Body Fat Percentage, Muscle Mass, and any daily activity stats like Steps.
        
        Return a valid JSON object with the following structure (use null if not found):
        {
            "weight_kg": 75.5,
            "body_fat_percentage": 15.2,
            "muscle_mass_kg": 60.1,
            "steps": 5000,
            "notes": "Extracted from Apple Health/Google Fit screenshot"
        }
        """
        
        try:
            sample_file = genai.upload_file(path=image_path, display_name="Health App Screenshot")
            
            response = await self._generate_with_retry([prompt, sample_file])
            
            if not response:
                return None

            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
                
            return json.loads(text_response)
        except Exception as e:
            logger.error(f"Error analyzing app screenshot: {e}")
            return None