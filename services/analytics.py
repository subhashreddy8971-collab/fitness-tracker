from sqlalchemy import func
from datetime import datetime, date
from database.models import Meal, Workout, BodyMetric, DailySummary, User
from database.db import SessionLocal

def get_daily_totals(user_id: int, target_date: date = None):
    """Calculates total calories and macros for a specific date."""
    if target_date is None:
        target_date = datetime.utcnow().date()
        
    db = SessionLocal()
    try:
        # Aggregate Meals
        meals = db.query(
            func.sum(Meal.calories).label("total_calories"),
            func.sum(Meal.protein).label("total_protein"),
            func.sum(Meal.carbs).label("total_carbs"),
            func.sum(Meal.fats).label("total_fats")
        ).filter(
            Meal.user_id == user_id,
            func.date(Meal.timestamp) == target_date
        ).first()

        # Aggregate Workouts
        workouts = db.query(
            func.count(Workout.id).label("count"),
            func.sum(Workout.calories_burned).label("total_burned")
        ).filter(
            Workout.user_id == user_id,
            func.date(Workout.timestamp) == target_date
        ).first()

        # Get latest weight for that day (or most recent)
        weight_metric = db.query(BodyMetric).filter(
            BodyMetric.user_id == user_id,
            func.date(BodyMetric.timestamp) <= target_date
        ).order_by(BodyMetric.timestamp.desc()).first()

        totals = {
            "calories_in": meals.total_calories or 0.0,
            "protein": meals.total_protein or 0.0,
            "carbs": meals.total_carbs or 0.0,
            "fats": meals.total_fats or 0.0,
            "calories_out": workouts.total_burned or 0.0,
            "workout_count": workouts.count or 0,
            "weight": weight_metric.weight_kg if weight_metric else None
        }
        
        # Update or Create DailySummary record
        summary = db.query(DailySummary).filter(
            DailySummary.user_id == user_id,
            DailySummary.date == target_date
        ).first()

        if not summary:
            summary = DailySummary(user_id=user_id, date=target_date)
            db.add(summary)

        summary.total_calories_in = totals["calories_in"]
        summary.total_calories_out = totals["calories_out"]
        summary.total_protein = totals["protein"]
        summary.workout_count = totals["workout_count"]
        summary.weight_kg = totals["weight"]
        
        db.commit()
        return totals
    finally:
        db.close()
