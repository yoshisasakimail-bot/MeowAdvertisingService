import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Token
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Google Sheets Configuration
    GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY")
    SHEET_ID = os.getenv("SHEET_ID")
    
    # Admin ID (can be multiple admins)
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    
    # Webhook Configuration
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    PORT = int(os.getenv("PORT", 5000))
    
    # Database (for storing user levels - using Google Sheets as database)
    USERS_SHEET_NAME = "Users"
    PAYMENTS_SHEET_NAME = "Payments"
    ABOUT_SHEET_NAME = "About"
