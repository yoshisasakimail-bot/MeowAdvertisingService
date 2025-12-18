import gspread
from google.oauth2.service_account import Credentials
import json
from config import Config

class GoogleSheetsManager:
    def __init__(self):
        self.setup_connection()
    
    def setup_connection(self):
        """Setup Google Sheets connection"""
        try:
            # Parse credentials from environment variable
            credentials_dict = json.loads(Config.GOOGLE_SHEETS_CREDENTIALS)
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_info(
                credentials_dict, 
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(Config.SHEET_ID).sheet1
            
            print("✅ Google Sheets connection established")
            
        except Exception as e:
            print(f"❌ Google Sheets connection error: {e}")
            self.sheet = None
    
    def add_user(self, user_data):
        """Add user to Google Sheets"""
        if not self.sheet:
            return False
            
        try:
            # Get next empty row
            next_row = len(self.sheet.get_all_values()) + 1
            
            # Prepare data
            row_data = [
                user_data.get('user_id', ''),
                user_data.get('username', ''),
                user_data.get('first_name', ''),
                user_data.get('plan', ''),
                user_data.get('amount', ''),
                user_data.get('payment_method', ''),
                user_data.get('payment_proof', ''),
                user_data.get('status', 'pending'),
                user_data.get('joined_date', ''),
                user_data.get('expiry_date', '')
            ]
            
            # Insert data
            self.sheet.insert_row(row_data, next_row)
            return True
            
        except Exception as e:
            print(f"Error adding user to sheet: {e}")
            return False
    
    def update_user_status(self, user_id, status):
        """Update user status in sheet"""
        if not self.sheet:
            return False
            
        try:
            # Find user row
            cell = self.sheet.find(str(user_id))
            if cell:
                # Update status column (column H)
                self.sheet.update_cell(cell.row, 8, status)
                return True
        except Exception as e:
            print(f"Error updating user status: {e}")
        
        return False
    
    def check_user_access(self, user_id):
        """Check if user has access"""
        if not self.sheet:
            return False
            
        try:
            cell = self.sheet.find(str(user_id))
            if cell:
                # Get status from column H
                status = self.sheet.cell(cell.row, 8).value
                return status == 'approved'
        except:
            pass
        
        return False
