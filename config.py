import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Admin User IDs (comma separated)
    ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    
    # Google Sheets Configuration
    GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    SHEET_ID = os.getenv("SHEET_ID")
    
    # Payment Information
    PAYMENT_METHODS = {
        "kbz_pay": "KBZ Pay - 09XXXXXXXX",
        "wave_pay": "Wave Pay - 09XXXXXXXX",
        "aya_pay": "Aya Pay - 09XXXXXXXX",
        "cb_pay": "CB Pay - 09XXXXXXXX"
    }
    
    # Service Plans
    SERVICE_PLANS = {
        "level1": {
            "name": "Advertising Lv.1",
            "price": "10,000 MMK",
            "duration": "7 days",
            "features": ["Feature 1", "Feature 2", "Feature 3"]
        },
        "level2": {
            "name": "Advertising Lv.2", 
            "price": "20,000 MMK",
            "duration": "14 days",
            "features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4"]
        },
        "level3": {
            "name": "Advertising Lv.3",
            "price": "30,000 MMK",
            "duration": "30 days",
            "features": ["All Features", "Priority Support", "Extra Benefits"]
        }
    }
