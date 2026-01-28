# AI Fitness & Nutrition Tracker Bot

A Telegram bot that uses Gemini Vision API to track your workouts and meals, providing intelligent insights and recommendations.

## Features

- **📸 Visual Logging**: Simply take a photo of your meal or gym equipment/exercise.
- **🧠 AI Analysis**: Gemini Vision API analyzes the photos to estimate calories, macros, exercise types, and form.
- **📊 Database**: Stores all your data in a structured SQL database (PostgreSQL/SQLite).
- **🤖 Telegram Interface**: Easy-to-use commands for logging and tracking.

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    - Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    - Edit `.env` and add your keys:
        - `TELEGRAM_BOT_TOKEN`: Get this from @BotFather on Telegram.
        - `GEMINI_API_KEY`: Get this from Google AI Studio.
        - `DATABASE_URL`: (Optional) Defaults to a local SQLite file `fitness_tracker.db` if not provided.

## Usage

1.  **Run the Bot**:
    ```bash
    python main.py
    ```
2.  **Telegram Commands**:
    - `/start`: Create your profile.
    - `/log_meal`: Upload a food photo to track calories/macros.
    - `/log_workout`: Upload a workout photo to track exercises/sets/reps.
    - `/cancel`: Cancel the current action.

## Project Structure

- `bot/`: Contains Telegram handlers and Gemini analysis logic.
- `database/`: Database models and connection setup.
- `images/`: Local storage for uploaded photos.
- `main.py`: Entry point for the application.
