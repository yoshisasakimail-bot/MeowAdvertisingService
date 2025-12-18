import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Config (Environment Variables) ---
TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GSPREAD_SERVICE_ACCOUNT')

# --- Google Sheets Connection ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    if SERVICE_ACCOUNT_JSON:
        creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # Local development backup
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    user_sheet = spreadsheet.get_worksheet(0)    # Sheet 1: User Data
    payment_sheet = spreadsheet.get_worksheet(1) # Sheet 2: Payment Data
except Exception as e:
    print(f"Connection Error: {e}")

# --- Helper Functions ---

def get_payment_details():
    """Sheet 2 မှ ငွေလွဲရန် အချက်အလက်ကို ဆွဲထုတ်ခြင်း"""
    try:
        data = payment_sheet.get_all_values()
        if len(data) > 1:
            phone = data[1][0] # Cell A2
            name = data[1][1]  # Cell B2
            return f"💰 **Payment Methods**\n\nName: {name}\nPhone: {phone}\n\nPlease send a screenshot of your receipt after payment."
        return "No payment info found in Google Sheets."
    except:
        return "System error: Could not fetch payment data."

async def show_services(update: Update, is_callback=False):
    """ဝန်ဆောင်မှု Button ၅ ခုကို ပြသခြင်း"""
    buttons = [
        [InlineKeyboardButton("Advertising Info", callback_data='info')],
        [InlineKeyboardButton("Advertising Setting", callback_data='setting')],
        [InlineKeyboardButton("Users Info", callback_data='users')],
        [InlineKeyboardButton("Payment Method", callback_data='payment')],
        [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    text = "Select a service from the list below:"
    
    if is_callback:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Advertising Service"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome! Press the button below to start.",
        reply_markup=reply_markup
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Advertising Service":
        # Google Sheet ထဲသို့ User Data သိမ်းဆည်းခြင်း
        user = update.effective_user
        try:
            user_sheet.append_row([str(user.id), user.first_name, f"@{user.username}"])
        except:
            pass # Google Sheet Error ဖြစ်လျှင်လည်း Bot ဆက်ပတ်နိုင်ရန်
        
        await show_services(update)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    back_btn = [[InlineKeyboardButton("Back", callback_data='back_to_list')]]
    reply_markup = InlineKeyboardMarkup(back_btn)

    if query.data == 'info':
        await query.edit_message_text("ℹ️ **Advertising Info**\nThis is where you explain your services.", reply_markup=reply_markup)
    
    elif query.data == 'setting':
        await query.edit_message_text("⚙️ **Advertising Setting**\nManage your campaign settings here.", reply_markup=reply_markup)
    
    elif query.data == 'users':
        await query.edit_message_text(f"👤 **User Info**\nYour ID: {query.from_user.id}\nStatus: Recorded.", reply_markup=reply_markup)
    
    elif query.data == 'payment':
        msg = get_payment_details()
        await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    
    elif query.data == 'back_to_list':
        await show_services(update, is_callback=True)
    
    elif query.data == 'back_to_menu':
        await query.message.reply_text("Returning to main menu...", reply_markup=ReplyKeyboardMarkup([["Advertising Service"]], resize_keyboard=True))

# --- Application Setup ---

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN not found!")
        return

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("Bot is running perfectly...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
