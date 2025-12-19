import os
import json
import gspread
import logging
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GSPREAD_SERVICE_ACCOUNT')
RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL') # Render URL: https://your-app.onrender.com
PORT = int(os.environ.get("PORT", 8080))

# --- Google Sheets Connection ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    
    user_sheet = spreadsheet.worksheet("user")
    payment_sheet = spreadsheet.worksheet("payment")
    admin_sheet = spreadsheet.worksheet("admin_id")
    logger.info("Connected to Google Sheets successfully.")
except Exception as e:
    logger.error(f"Sheet Connection Error: {e}")

# --- Helper Functions ---
def get_admin_id():
    try:
        val = admin_sheet.acell('A2').value
        return int(val) if val else None
    except: return None

def is_member(user_id):
    try:
        cell = user_sheet.find(str(user_id))
        row = user_sheet.row_values(cell.row)
        return len(row) >= 4 and row[3].strip().lower() == "member"
    except: return False

def get_main_keyboard(user_id):
    buttons = [["Meow Advertising service"]]
    if is_member(user_id):
        buttons.append(["Advertising Ads"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        if not user_sheet.find(str(user.id)):
            user_sheet.append_row([str(user.id), user.first_name, f"@{user.username}", "Free"])
    except: pass
    await update.message.reply_text(f"Hello {user.first_name}!", reply_markup=get_main_keyboard(user.id))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    if text == "Meow Advertising service":
        buttons = [
            [InlineKeyboardButton("About Service", callback_data='about')],
            [InlineKeyboardButton("Payment Method", callback_data='payment_list')]
        ]
        await update.message.reply_text("ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'payment_list':
        buttons = [[InlineKeyboardButton("Lv 1 - 5000 MMK", callback_data='pay_lv1')], [InlineKeyboardButton("Back", callback_data='main_services')]]
        await query.edit_message_text("ဈေးနှုန်းများ -", reply_markup=InlineKeyboardMarkup(buttons))
    elif query.data.startswith('pay_lv'):
        try:
            phone = payment_sheet.acell('A2').value
            name = payment_sheet.acell('B2').value
            await query.edit_message_text(f"💳 KBZ/Wave: `{phone}`\nName: {name}", parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ Payment data loading error.")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = get_admin_id()
    if admin_id and update.message.photo:
        await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=f"New Receipt from {update.effective_user.first_name}")
        await update.message.reply_text("✅ Admin ထံ ပို့ပြီးပါပြီ။")

# --- Webhook Server ---
app_server = Flask(__name__)
@app_server.route('/' + TOKEN, methods=['POST'])
async def webhook_handler():
    # ဒီအပိုင်းက Webhook အတွက်ဖြစ်ပါတယ်
    return "OK"

# --- Main ---
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    application.add_handler(CallbackQueryHandler(handle_buttons))

    # Webhook စနစ်ကို အသုံးပြုခြင်း (Render အတွက် အကောင်းဆုံး)
    if RENDER_URL:
        # ဤနေရာတွင် meowpremium ကဲ့သို့ webhook run ပါမည်
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_URL}/{TOKEN}"
        )
    else:
        # Local တွင်စမ်းသပ်ရန် Polling သုံးပါမည်
        application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
