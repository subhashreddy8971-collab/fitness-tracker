import re

# Simple local cache for common foods (per 100g) and exercises (cal/min)
# In production, this would be a database table
FOOD_CACHE = {
    "chicken": {"cals": 165, "prot": 31, "carbs": 0, "fat": 3.6},
    "chicken breast": {"cals": 165, "prot": 31, "carbs": 0, "fat": 3.6},
    "rice": {"cals": 130, "prot": 2.7, "carbs": 28, "fat": 0.3},
    "white rice": {"cals": 130, "prot": 2.7, "carbs": 28, "fat": 0.3},
    "egg": {"cals": 155, "prot": 13, "carbs": 1.1, "fat": 11},
    "eggs": {"cals": 155, "prot": 13, "carbs": 1.1, "fat": 11},
    "beef": {"cals": 250, "prot": 26, "carbs": 0, "fat": 17},
    "steak": {"cals": 271, "prot": 25, "carbs": 0, "fat": 19},
    "potato": {"cals": 77, "prot": 2, "carbs": 17, "fat": 0.1},
    "oats": {"cals": 389, "prot": 16.9, "carbs": 66, "fat": 6.9},
    "milk": {"cals": 42, "prot": 3.4, "carbs": 5, "fat": 1},
    "banana": {"cals": 89, "prot": 1.1, "carbs": 22.8, "fat": 0.3},
    "apple": {"cals": 52, "prot": 0.3, "carbs": 14, "fat": 0.2},
    "bread": {"cals": 265, "prot": 9, "carbs": 49, "fat": 3.2},
}

EXERCISE_CACHE = {
    "run": 10,  # cal/min
    "running": 10,
    "walk": 4,
    "walking": 4,
    "cycling": 8,
    "bike": 8,
    "yoga": 3,
    "pilates": 3.5,
    "swimming": 10,
    "swim": 10
}

class SmartParser:
    @staticmethod
    def parse_food(text):
        """
        Tries to parse '250g chicken' patterns.
        Returns dict with macros if successful, None otherwise.
        """
        text = text.lower().strip()
        
        # Regex for "100g food" or "100 ml food"
        match = re.search(r'(\d+)\s*(?:g|ml|oz)?\s+([a-zA-Z\s]+)', text)
        if match:
            try:
                amount = float(match.group(1))
                food_name = match.group(2).strip()
                
                # Check cache (partial match)
                # e.g. "grilled chicken" -> matches "chicken"
                cache_hit = None
                for key in FOOD_CACHE:
                    if key in food_name or food_name in key:
                        cache_hit = FOOD_CACHE[key]
                        food_name = key # normalize name
                        break
                
                if cache_hit:
                    ratio = amount / 100.0
                    return {
                        "food_name": food_name.title(),
                        "weight_grams": amount,
                        "calories": round(cache_hit["cals"] * ratio),
                        "protein": round(cache_hit["prot"] * ratio, 1),
                        "carbs": round(cache_hit["carbs"] * ratio, 1),
                        "fats": round(cache_hit["fat"] * ratio, 1),
                        "source": "smart_cache"
                    }
            except:
                pass
        return None

    @staticmethod
    def parse_workout(text):
        """
        Tries to parse '30 min run' patterns.
        """
        text = text.lower().strip()
        
        # Regex for "30 min run"
        match = re.search(r'(\d+)\s*(?:min|mins|minutes)?\s+([a-zA-Z\s]+)', text)
        if match:
            try:
                duration = float(match.group(1))
                exercise_name = match.group(2).strip()
                
                # Check cache
                rate = 5 # Default burn rate
                for key in EXERCISE_CACHE:
                    if key in exercise_name:
                        rate = EXERCISE_CACHE[key]
                        break
                
                return {
                    "exercise_name": exercise_name.title(),
                    "duration_minutes": duration,
                    "calories_burned": round(duration * rate),
                    "source": "smart_cache"
                }
            except:
                pass
        return None
