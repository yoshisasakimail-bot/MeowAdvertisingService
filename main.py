import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask
import threading

# --- Render Setup ---
server = Flask(__name__)
@server.route('/')
def home(): return "Bot is Running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- Config & Google Sheets ---
TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GSPREAD_SERVICE_ACCOUNT')

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SHEET_ID)

user_sheet = spreadsheet.get_worksheet(0)    # Sheet1: Users
payment_sheet = spreadsheet.get_worksheet(1) # Sheet2: Payment Info
admin_sheet = spreadsheet.get_worksheet(2)   # Sheet3: Admin Settings (အသစ်)

# --- Helper Functions ---

def get_admin_id():
    """Sheet3 ရဲ့ A2 Cell ကနေ Admin ID ကို ဖတ်ယူခြင်း"""
    try:
        val = admin_sheet.cell(2, 1).value
        return int(val) if val else None
    except:
        return None

def is_member(user_id):
    try:
        cell = user_sheet.find(str(user_id))
        row = user_sheet.row_values(cell.row)
        return len(row) >= 4 and row[3] == "Member"
    except: return False

def get_main_keyboard(user_id):
    buttons = [["Meow Advertising service"]]
    if is_member(user_id):
        buttons.append(["Advertising Ads"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"Hello {user.first_name}, Meow Advertising service မှ ကြိုဆိုပါတယ်။"
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(user.id))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user

    if text == "Meow Advertising service":
        buttons = [
            [InlineKeyboardButton("Advertising Service About", callback_data='about')],
            [InlineKeyboardButton("User Info", callback_data='user_info')],
            [InlineKeyboardButton("Payment Method", callback_data='payment_list')]
        ]
        await update.message.reply_text("ဝန်ဆောင်မှုများ ရယူရန် ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "Advertising Ads":
        if is_member(user.id):
            await update.message.reply_text("Welcome to Member Ads Area! 🎉")
        else:
            await update.message.reply_text("သင်သည် Member မဟုတ်သေးပါ။")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'about':
        about_text = "📖 **Service Guide**\nLv 1 မှ Lv 3 အထိ အသုံးပြုပုံရှင်းလင်းချက်...\n(ဒီနေရာမှာ စိတ်ကြိုက်စာရေးပါ)"
        await query.edit_message_text(about_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='main_services')]]))

    elif query.data == 'payment_list':
        prices = [
            [InlineKeyboardButton("Lv 1 - 5000 MMK", callback_data='pay_lv1')],
            [InlineKeyboardButton("Lv 2 - 10000 MMK", callback_data='pay_lv2')],
            [InlineKeyboardButton("Lv 3 - 20000 MMK", callback_data='pay_lv3')],
            [InlineKeyboardButton("Back", callback_data='main_services')]
        ]
        await query.edit_message_text("ဈေးနှုန်းများ ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(prices))

    elif query.data.startswith('pay_lv'):
        lv = query.data.replace('pay_', '')
        # Payment info ကိုလည်း Sheet2 ကနေ ဆွဲယူနိုင်ပါတယ်
        pay_info = f"💳 **Payment ({lv.upper()})**\n\nKBZ Pay/Wave: 09xxxxxx\nName: Admin Name\n\nငွေလွှဲပြေစာ ပို့ပေးပါ။"
        await query.edit_message_text(pay_info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='payment_list')]]))

    elif query.data == 'main_services':
        buttons = [[InlineKeyboardButton("Advertising Service About", callback_data='about')],
                   [InlineKeyboardButton("User Info", callback_data='user_info')],
                   [InlineKeyboardButton("Payment Method", callback_data='payment_list')]]
        await query.edit_message_text("ဝန်ဆောင်မှုများ ရယူရန် ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပြေစာကို Sheet ထဲက Admin ID ထံ ပို့ပေးခြင်း"""
    if update.message.photo:
        admin_id = get_admin_id()
        if not admin_id:
            await update.message.reply_text("Error: Admin မသတ်မှတ်ရသေးပါ။")
            return

        user = update.effective_user
        caption = f"📩 **New Payment Receipt**\nFrom: {user.first_name}\nID: `{user.id}`\n\nSheet တွင် Status ကို 'Member' ဟု ပြောင်းပေးပါ။"
        
        await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=caption, parse_mode="Markdown")
        await update.message.reply_text("ပြေစာကို Admin ထံ ပို့လိုက်ပါပြီ။ စစ်ဆေးပြီးပါက Member Ads ခလုတ် ပေါ်လာပါမည်။")

# --- Main ---
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    print("Bot is started with Sheet-based Admin ID.")
    app.run_polling()

if __name__ == '__main__':
    main()
    
