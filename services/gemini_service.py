import google.generativeai as genai
import logging
import json
import asyncio
from config import GEMINI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        # Use flash model for speed and cost efficiency
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')

    async def _generate_with_retry(self, inputs):
        """Helper to run generation with retry logic."""
        max_retries = 2
        delay = 5 

        for attempt in range(max_retries):
            try:
                await asyncio.sleep(2) # Throttle to prevent rate limits
                response = await asyncio.to_thread(self.model.generate_content, inputs)
                return response
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower():
                    logger.warning(f"Rate limit hit on attempt {attempt+1}")
                    if attempt == max_retries - 1:
                        return "RATE_LIMIT"
                else:
                    logger.warning(f"Gemini API attempt {attempt+1} failed: {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
        return None

    async def analyze_image(self, image_path, caption=""):
        """
        Analyzes image (Food, Workout, or Data).
        Returns JSON.
        """
        prompt = f"""
        Analyze this image for a fitness app.
        Context/Caption: "{caption}"

        Identify what it is:
        1. Meal: Name, weight est., calories, macros.
        2. Workout: Exercise name, sets/reps/duration, calories burned est.
        3. App Screenshot/Scale: Weight, steps, etc.
        4. Other: Unknown.

        Return ONLY raw JSON:
        {{
            "type": "meal" | "workout" | "metric" | "unknown",
            "reply": "Friendly conversational response for the user (e.g., 'Yum! That burger looks great. Logged it.')",
            "data": {{ ...extracted fields... }}
        }}
        """
        
        try:
            sample_file = genai.upload_file(path=image_path, display_name="User Upload")
            response = await self._generate_with_retry([prompt, sample_file])
            
            if response == "RATE_LIMIT":
                return {"type": "error", "reply": "My brain is tired (Rate Limit). Please try again in 1 minute! 🧠💤"}
            
            if response:
                text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
        except Exception as e:
            logger.error(f"Vision error: {e}")
        return None

    async def chat(self, user_text, context_str):
        """
        Conversational response with database context.
        """
        final_prompt = f"""
        Role: Fitness Coach. Tone: Encouraging, concise.
        User Data/Stats: {context_str}
        
        User Query: {user_text}
        
        Answer the user naturally. Use the data to be specific.
        """
        
        response = await self._generate_with_retry(final_prompt)
        
        if response == "RATE_LIMIT":
            return "My brain is tired (Rate Limit). Please try again in 1 minute! 🧠💤"
            
        return response.text if response else "I'm having trouble thinking right now. Try again?"