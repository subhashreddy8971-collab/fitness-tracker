import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage
import os
from database.db import SessionLocal
from database.models import Workout, Meal, DailySummary

# Set non-interactive backend for matplotlib
plt.switch_backend('Agg')

def generate_excel_report(user_id):
    """Generates an Excel report with data sheets and charts."""
    # Ensure directories exist
    os.makedirs("exports", exist_ok=True)
    os.makedirs("images/plots", exist_ok=True)
    
    filename = f"exports/fitness_report_{user_id}.xlsx"
    db = SessionLocal()
    
    try:
        # 1. Fetch Daily Summary Data
        summaries = db.query(DailySummary).filter(DailySummary.user_id == user_id).order_by(DailySummary.date).all()
        data_summary = [{
            "Date": s.date, 
            "Calories In": s.total_calories_in, 
            "Calories Out": s.total_calories_out,
            "Protein (g)": s.total_protein,
            "Weight (kg)": s.weight_kg
        } for s in summaries]
        df_summary = pd.DataFrame(data_summary)
        
        # 2. Fetch Meals Data
        meals = db.query(Meal).filter(Meal.user_id == user_id).order_by(Meal.timestamp).all()
        data_meals = [{
            "Time": m.timestamp.strftime("%Y-%m-%d %H:%M"),
            "Food": m.food_name,
            "Calories": m.calories,
            "Protein": m.protein,
            "Carbs": m.carbs,
            "Fats": m.fats,
            "Notes": m.notes
        } for m in meals]
        df_meals = pd.DataFrame(data_meals)

        # 3. Fetch Workouts Data
        workouts = db.query(Workout).filter(Workout.user_id == user_id).order_by(Workout.timestamp).all()
        data_workouts = [{
            "Time": w.timestamp.strftime("%Y-%m-%d %H:%M"),
            "Exercise": w.exercise_name,
            "Sets": w.sets,
            "Reps": w.reps,
            "Calories Burned": w.calories_burned,
            "Notes": w.notes
        } for w in workouts]
        df_workouts = pd.DataFrame(data_workouts)
        
        # Write to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            if not df_summary.empty:
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
            else:
                pd.DataFrame({'Info': ['No summary data yet']}).to_excel(writer, sheet_name='Summary', index=False)
                
            if not df_meals.empty:
                df_meals.to_excel(writer, sheet_name='Meals', index=False)
            
            if not df_workouts.empty:
                df_workouts.to_excel(writer, sheet_name='Workouts', index=False)
            
        # Generate Charts if data exists
        if not df_summary.empty:
            wb = load_workbook(filename)
            ws = wb['Summary']
            
            # Plot 1: Calories In vs Out
            plt.figure(figsize=(10, 6))
            plt.plot(df_summary['Date'], df_summary['Calories In'], label='Calories In', marker='o', color='skyblue')
            plt.plot(df_summary['Date'], df_summary['Calories Out'], label='Calories Out', marker='x', color='salmon')
            plt.title('Calories: In vs Out')
            plt.xlabel('Date')
            plt.ylabel('Calories')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            plot_path_cals = f"images/plots/cals_{user_id}.png"
            plt.savefig(plot_path_cals)
            plt.close()
            
            # Insert into Excel
            img = ExcelImage(plot_path_cals)
            ws.add_image(img, 'H2') # Place next to data
            
            # Plot 2: Weight Trend
            valid_weight = df_summary.dropna(subset=['Weight (kg)'])
            if not valid_weight.empty:
                plt.figure(figsize=(10, 6))
                plt.plot(valid_weight['Date'], valid_weight['Weight (kg)'], color='green', marker='s', linestyle='-')
                plt.title('Weight Trend')
                plt.xlabel('Date')
                plt.ylabel('Weight (kg)')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                plot_path_weight = f"images/plots/weight_{user_id}.png"
                plt.savefig(plot_path_weight)
                plt.close()
                
                img2 = ExcelImage(plot_path_weight)
                ws.add_image(img2, 'H35') # Place below the first chart

            wb.save(filename)
            
        return filename

    finally:
        db.close()
