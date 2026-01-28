import google.generativeai as genai
from sqlalchemy import func
from datetime import datetime, timedelta
from database.db import SessionLocal
from database.models import User, DailySummary, Workout, Meal
from config import GEMINI_API_KEY
import logging
import asyncio

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
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
                    logger.error(f"Gemini API Error: {e}")
                    return None
        return None

    def get_user_history(self, user_id, days=7):
        db = SessionLocal()
        try:
            start_date = datetime.utcnow().date() - timedelta(days=days)
            
            summaries = db.query(DailySummary).filter(
                DailySummary.user_id == user_id,
                DailySummary.date >= start_date
            ).all()
            
            # Get recent specific meals to understand preferences
            recent_meals = db.query(Meal).filter(
                Meal.user_id == user_id,
                Meal.timestamp >= datetime.utcnow() - timedelta(days=3)
            ).order_by(Meal.timestamp.desc()).limit(10).all()

            # Get recent workouts
            recent_workouts = db.query(Workout).filter(
                Workout.user_id == user_id,
                Workout.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).order_by(Workout.timestamp.desc()).limit(5).all()
            
            return {
                "summaries": summaries,
                "recent_meals": [m.food_name for m in recent_meals],
                "recent_workouts": [w.exercise_name for w in recent_workouts]
            }
        finally:
            db.close()

    async def generate_recommendations(self, user_id):
        history = self.get_user_history(user_id)
        
        # Calculate averages
        total_cals = sum(s.total_calories_in for s in history['summaries'])
        total_protein = sum(s.total_protein for s in history['summaries'])
        days_count = len(history['summaries']) if history['summaries'] else 1
        
        avg_cals = total_cals / days_count
        avg_protein = total_protein / days_count
        
        prompt = f"""
        Act as an expert fitness and nutrition coach.
        Based on the user's recent data (Last {days_count} days), generate a personalized plan for TOMORROW.
        
        DATA:
        - Average Daily Calories: {avg_cals:.0f} kcal
        - Average Daily Protein: {avg_protein:.0f} g
        - Recent Meals: {', '.join(history['recent_meals'])}
        - Recent Workouts: {', '.join(history['recent_workouts'])}
        
        TASK:
        1. Analyze their current trends (Are they eating enough protein? Consistent with workouts?).
        2. Suggest a specific Meal Plan for tomorrow (Breakfast, Lunch, Dinner, Snack) that complements their habits but improves nutrition.
        3. Suggest a specific Workout Routine for tomorrow (considering what they did recently to avoid overtraining same muscles).
        
        FORMAT:
        Use clear headings (## Analysis, ## Meal Plan, ## Workout). Keep it concise and motivating.
        """
        
        response = await self._generate_with_retry(prompt)
        
        if response:
            return response.text
        else:
            return "Sorry, I couldn't generate recommendations right now. Please try tracking more data first!"