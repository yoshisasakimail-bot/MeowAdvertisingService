import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleSheetsHandler:
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(
            self.get_credentials(), self.scope
        )
        self.client = gspread.authorize(self.creds)
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
    def get_credentials(self):
        # Get credentials from environment variable
        import json
        creds_json = os.getenv('GOOGLE_CREDENTIALS')
        return json.loads(creds_json)
    
    def check_user_access(self, user_id):
        """Check if user has access in Google Sheets"""
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet("Users")
            
            # Find user in sheet
            records = worksheet.get_all_records()
            
            for record in records:
                if str(record.get('user_id')) == str(user_id):
                    return record.get('access', False)
            
            return False
        except Exception as e:
            print(f"Error accessing Google Sheets: {e}")
            return False
    
    def add_user(self, user_id, username, plan):
        """Add new user to sheet"""
        try:
            sheet = self.client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet("Users")
            
            worksheet.append_row([
                user_id,
                username,
                plan,
                False,  # access
                False,  # payment_confirmed
                False   # admin_unlocked
            ])
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
