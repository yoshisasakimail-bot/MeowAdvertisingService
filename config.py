import os
import json

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # Google Sheets Configuration
    GOOGLE_SHEET_KEY_JSON = os.getenv("GOOGLE_SHEET_KEY", "{}")
    
    # Parse JSON string to dict
    try:
        GOOGLE_SHEET_KEY = json.loads(GOOGLE_SHEET_KEY_JSON)
    except json.JSONDecodeError:
        GOOGLE_SHEET_KEY = {}
    
    SHEET_ID = os.getenv("SHEET_ID", "")
    
    # Admin IDs (can be multiple admins)
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = []
    if admin_ids_str:
        for admin_id in admin_ids_str.split(","):
            admin_id = admin_id.strip()
            if admin_id.isdigit():
                ADMIN_IDS.append(int(admin_id))
    
    # Webhook Configuration
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    PORT = int(os.getenv("PORT", 5000))
    
    # Database (for storing user levels - using Google Sheets as database)
    USERS_SHEET_NAME = "Users"
    PAYMENTS_SHEET_NAME = "Payments"
    ABOUT_SHEET_NAME = "About"
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if not cls.GOOGLE_SHEET_KEY:
            errors.append("GOOGLE_SHEET_KEY is required or invalid")
        
        if not cls.SHEET_ID:
            errors.append("SHEET_ID is required")
        
        if not cls.ADMIN_IDS:
            print("Warning: No ADMIN_IDS configured")
        
        if errors:
            raise ValueError("Configuration errors: " + ", ".join(errors))

# Validate configuration when module is imported
try:
    Config.validate_config()
    print("✅ Configuration loaded successfully")
except ValueError as e:
    print(f"❌ {e}")
