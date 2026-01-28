import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from database.db import SessionLocal
from database.models import User, Meal, Workout, BodyMetric
from services.smart_parser import SmartParser
from services.gemini_service import GeminiService
from services.analytics import get_daily_totals

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

gemini = GeminiService()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unified handler for text and photos."""
    user = update.effective_user
    db = SessionLocal()
    
    # 1. Get/Create User
    db_user = db.query(User).filter(User.telegram_id == user.id).first()
    if not db_user:
        db_user = User(telegram_id=user.id, name=user.full_name)
        db.add(db_user)
        db.commit()

    response_text = ""
    
    # 2. HANDLE PHOTOS (Always use AI)
    if update.message.photo:
        await update.message.reply_chat_action("upload_photo")
        
        # Download
        photo_file = await update.message.photo[-1].get_file()
        os.makedirs("images", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"images/upload_{user.id}_{timestamp}.jpg"
        await photo_file.download_to_drive(file_path)
        
        # Analyze
        caption = update.message.caption or ""
        result = await gemini.analyze_image(file_path, caption)
        
        if result:
            r_type = result.get('type')
            data = result.get('data', {})
            reply = result.get('reply', 'Processed.')
            
            if r_type == 'meal':
                m = Meal(user_id=db_user.id, image_path=file_path, **data)
                db.add(m)
                response_text = f"✅ {reply}"
            elif r_type == 'workout':
                w = Workout(user_id=db_user.id, image_path=file_path, **data)
                db.add(w)
                response_text = f"💪 {reply}"
            elif r_type == 'metric':
                if 'weight_kg' in data:
                    bm = BodyMetric(user_id=db_user.id, weight_kg=data['weight_kg'], source='gemini_vision')
                    db.add(bm)
                response_text = f"📊 {reply}"
            else:
                response_text = reply
            
            db.commit()
        else:
            response_text = "Sorry, I couldn't analyze that photo."

    # 3. HANDLE TEXT
    elif update.message.text:
        text = update.message.text.strip()
        
        # A. Local Greeting (Zero Cost)
        if text.lower() in ['/start', 'hi', 'hello', 'hey', 'help']:
            response_text = (
                f"Hey {user.first_name}! 👋\n"
                "I'm ready to track. Just send me:\n"
                "📸 Photos of food or workouts\n"
                "📝 Text like 'ate 2 eggs' or 'ran 20 mins'\n"
                "❓ Questions like 'how am I doing?'"
            )
            await update.message.reply_text(response_text)
            db.close()
            return

        # B. Try Smart Parser (Zero Cost)
        food_data = SmartParser.parse_food(text)
        workout_data = SmartParser.parse_workout(text)
        
        if food_data:
            m = Meal(user_id=db_user.id, **food_data)
            db.add(m)
            db.commit()
            response_text = (
                f"✅ Logged: {food_data['food_name']}
"
                f"🔥 {food_data['calories']} cal | 🥩 {food_data['protein']}g protein"
            )
            
        elif workout_data:
            w = Workout(user_id=db_user.id, **workout_data)
            db.add(w)
            db.commit()
            response_text = (
                f"💪 Logged: {workout_data['exercise_name']}
"
                f"⏱ {workout_data['duration_minutes']} min | 🔥 {workout_data['calories_burned']} cal"
            )
            
        else:
            # B. Complex Query -> Gemini Chat
            await update.message.reply_chat_action("typing")
            
            # Build Context
            totals = get_daily_totals(db_user.id)
            context = (
                f"Date: {datetime.now().strftime('%A, %d %b')}
"
                f"Today's Stats:
"
                f"- Calories: {totals['calories_in']:.0f} In / {totals['calories_out']:.0f} Out
"
                f"- Protein: {totals['protein']:.1f}g
"
                f"- Workouts: {totals['workout_count']}
"
                f"- Current Weight: {totals['weight'] or 'Unknown'} kg"
            )
            
            response_text = await gemini.chat(text, context)

    db.close()
    
    # Send Final Response
    if response_text:
        await update.message.reply_text(response_text)
