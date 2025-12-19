import os
import json
import gspread
import logging
from flask import Flask
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
RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL') # Render URL ကို ဤနေရာတွင် သုံးမည်
PORT = int(os.environ.get("PORT", 8080))

# --- Google Sheets Connection ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    if SERVICE_ACCOUNT_JSON:
        creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        user_sheet = spreadsheet.worksheet("user")
        payment_sheet = spreadsheet.worksheet("payment")
        admin_sheet = spreadsheet.worksheet("admin_id")
        logger.info("Connected to Sheets: user, payment, admin_id")
except Exception as e:
    logger.error(f"Sheet Connection Error: {e}")

# --- Helper Functions ---
def get_admin_id():
    try:
        val = admin_sheet.acell('A2').value # A2 မှ Admin ID ကို တိုက်ရိုက်ဖတ်သည်
        return int(val) if val else None
    except: return None

def is_member(user_id):
    try:
        cell = user_sheet.find(str(user_id))
        row = user_sheet.row_values(cell.row)
        return len(row) >= 4 and row[3].strip().lower() == "member" # Column D ကို စစ်ဆေးသည်
    except: return False

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        if not user_sheet.find(str(user.id)):
            user_sheet.append_row([str(user.id), user.first_name, f"@{user.username}", "Free"])
    except: pass
    
    keyboard = [["Meow Advertising service"]]
    if is_member(user.id):
        keyboard.append(["Advertising Ads"])
    
    await update.message.reply_text(
        f"Hello {user.first_name}, Meow Advertising service မှ ကြိုဆိုပါတယ်။",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Meow Advertising service":
        buttons = [
            [InlineKeyboardButton("About Service", callback_data='about')],
            [InlineKeyboardButton("Payment Method", callback_data='payment_list')]
        ]
        await update.message.reply_text("ဝန်ဆောင်မှုများ ရယူရန် ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))
    elif text == "Advertising Ads" and is_member(update.effective_user.id):
        await update.message.reply_text("✨ Welcome to Member Advertising Ads! ✨")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'payment_list':
        buttons = [[InlineKeyboardButton("Lv 1 - 5000 MMK", callback_data='pay_lv1')],
                   [InlineKeyboardButton("Back", callback_data='main_services')]]
        await query.edit_message_text("ဈေးနှုန်းများ ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))
        
    elif query.data.startswith('pay_lv'):
        try:
            phone = payment_sheet.acell('A2').value # Payment အချက်အလက်များကို တိုက်ရိုက် Cell မှဖတ်သည်
            name = payment_sheet.acell('B2').value
            await query.edit_message_text(f"💳 **Payment Info**\n\nKBZ/Wave: `{phone}`\nName: {name}\n\nပြေစာ ပို့ပေးပါ။", parse_mode="Markdown")
        except:
            await query.edit_message_text("❌ Payment info error.")

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = get_admin_id()
    if admin_id and update.message.photo:
        await context.bot.send_photo(
            chat_id=admin_id, 
            photo=update.message.photo[-1].file_id, 
            caption=f"📩 Receipt from {update.effective_user.first_name} (ID: {update.effective_user.id})"
        )
        await update.message.reply_text("✅ ပြေစာကို Admin ထံ ပို့လိုက်ပါပြီ။")

# --- Main Runtime ---
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    application.add_handler(CallbackQueryHandler(handle_buttons))

    # Webhook စနစ် (meowpremium ကဲ့သို့ Render အတွက် အသုံးပြုခြင်း)
    if RENDER_EXTERNAL_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{RENDER_EXTERNAL_URL}/{TOKEN}"
        )
        logger.info(f"Webhook started at {RENDER_EXTERNAL_URL}")
    else:
        # Local တွင်စမ်းရန် Polling သုံးသည်
        application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
