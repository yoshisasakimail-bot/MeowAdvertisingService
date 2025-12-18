import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# --- Render အတွက် Flask Server အသေးစား (Port Error မတက်စေရန်) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Running"

def run_flask():
    # Render က ပေးတဲ့ Port ကို သုံးမယ်၊ မရှိရင် 8080 သုံးမယ်
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

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
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        user_sheet = spreadsheet.get_worksheet(0)
        payment_sheet = spreadsheet.get_worksheet(1)
    else:
        print("Missing GSPREAD_SERVICE_ACCOUNT variable")
except Exception as e:
    print(f"Connection Error: {e}")

# --- Bot Functions ---

def get_payment_details():
    try:
        data = payment_sheet.get_all_values()
        if len(data) > 1:
            phone = data[1][0]
            name = data[1][1]
            return f"💰 **Payment Methods**\n\nName: {name}\nPhone: {phone}\n\nPlease send a screenshot of your receipt after payment."
        return "No payment info found."
    except:
        return "Error fetching payment data."

async def show_services(update: Update, is_callback=False):
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Advertising Service"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome! Press the button below.", reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Advertising Service":
        user = update.effective_user
        try:
            user_sheet.append_row([str(user.id), user.first_name, f"@{user.username}"])
        except:
            pass
        await show_services(update)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    back_btn = [[InlineKeyboardButton("Back", callback_data='back_to_list')]]
    reply_markup = InlineKeyboardMarkup(back_btn)

    if query.data == 'info':
        await query.edit_message_text("ℹ️ Advertising Info section.", reply_markup=reply_markup)
    elif query.data == 'setting':
        await query.edit_message_text("⚙️ Advertising Setting section.", reply_markup=reply_markup)
    elif query.data == 'users':
        await query.edit_message_text(f"👤 Your ID: {query.from_user.id}", reply_markup=reply_markup)
    elif query.data == 'payment':
        await query.edit_message_text(get_payment_details(), reply_markup=reply_markup, parse_mode="Markdown")
    elif query.data == 'back_to_list':
        await show_services(update, is_callback=True)
    elif query.data == 'back_to_menu':
        await query.message.reply_text("Main Menu", reply_markup=ReplyKeyboardMarkup([["Advertising Service"]], resize_keyboard=True))

def main():
    # Flask Server ကို thread တစ်ခုနဲ့ background မှာ run မယ်
    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()


