import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_IDS = [123456789]  # Add your admin ID here
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    
    # Payment information
    PAYMENT_NUMBER = "09XXXXXXXXX"
    PAYMENT_NAME = "Admin Name"
    
    # Service prices
    PRICES = {
        'level1': 10000,
        'level2': 20000,
        'level3': 35000
    }
