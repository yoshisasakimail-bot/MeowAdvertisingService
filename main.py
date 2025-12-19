import os
import json
import gspread
import threading
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Render Web Service Setup ---
server = Flask(__name__)
@server.route('/')
def home(): 
    return "Bot is Active"

def run_flask():
    # Render တွင် Deploy အောင်မြင်ရန် PORT ကို ပတ်ဝန်းကျင်မှ ဖတ်ယူခြင်း
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- Configuration & Google Sheets Connection ---
TOKEN = os.environ.get('BOT_TOKEN')
SHEET_ID = os.environ.get('SHEET_ID')
SERVICE_ACCOUNT_JSON = os.environ.get('GSPREAD_SERVICE_ACCOUNT')

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    if SERVICE_ACCOUNT_JSON:
        creds_dict = json.loads(SERVICE_ACCOUNT_JSON)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Tab နာမည်များဖြင့် တိုက်ရိုက်ချိတ်ဆက်ခြင်း
        user_sheet = spreadsheet.worksheet("user")
        payment_sheet = spreadsheet.worksheet("payment")
        admin_sheet = spreadsheet.worksheet("admin_id")
        print("Connected to Sheets: user, payment, admin_id")
    else:
        print("GSPREAD_SERVICE_ACCOUNT is missing.")
except Exception as e:
    print(f"Sheet Connection Error: {e}")

# --- Helper Functions ---

def get_admin_id():
    """admin_id tab ရဲ့ A2 Cell မှ ID ကိုယူသည်"""
    try:
        val = admin_sheet.cell(2, 1).value
        return int(val) if val else None
    except: return None

def is_member(user_id):
    """user tab တွင် Member ဟုတ်မဟုတ် စစ်ဆေးသည်"""
    try:
        cell = user_sheet.find(str(user_id))
        row = user_sheet.row_values(cell.row)
        # Column D တွင် Member ဟု ရှိမရှိ စစ်ဆေးခြင်း
        return len(row) >= 4 and row[3].strip().lower() == "member"
    except: return False

def get_main_keyboard(user_id):
    buttons = [["Meow Advertising service"]]
    if is_member(user_id):
        buttons.append(["Advertising Ads"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        if not user_sheet.find(str(user.id)):
            user_sheet.append_row([str(user.id), user.first_name, f"@{user.username}", "Free"])
    except: pass

    welcome_msg = f"Hello {user.first_name}, Meow Advertising service မှ ကြိုဆိုပါတယ်။"
    await update.message.reply_text(welcome_msg, reply_markup=get_main_keyboard(user.id))

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
            await update.message.reply_text("✨ Welcome to Member Advertising Ads! ✨")
        else:
            await update.message.reply_text("🚫 သင်သည် Member မဟုတ်သေးပါ။")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'about':
        text = "📖 **Meow Advertising Guide**\n\nLv 1 မှ Lv 3 အထိ အသုံးပြုပုံများ...\n(ဒီမှာ စိတ်ကြိုက်စာရေးပါ)"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='main_services')]]), parse_mode="Markdown")

    elif query.data == 'payment_list':
        buttons = [
            [InlineKeyboardButton("Lv 1 - 5000 MMK", callback_data='pay_lv1')],
            [InlineKeyboardButton("Lv 2 - 10000 MMK", callback_data='pay_lv2')],
            [InlineKeyboardButton("Lv 3 - 20000 MMK", callback_data='pay_lv3')],
            [InlineKeyboardButton("Back", callback_data='main_services')]
        ]
        await query.edit_message_text("ဈေးနှုန်းများ ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))

    elif query.data.startswith('pay_lv'):
        lv = query.data.replace('pay_', '').upper()
        try:
            # တိုက်ရိုက် Cell မှ ဖတ်ခြင်းဖြင့် ပိုမိုမြန်ဆန်စေသည်
            phone = payment_sheet.acell('A2').value
            name = payment_sheet.acell('B2').value
            
            if phone and name:
                pay_msg = f"💳 **Payment for {lv}**\n\nKBZ/Wave: `{phone}`\nName: {name}\n\nငွေလွှဲပြေစာ ပို့ပေးပါ။"
            else:
                pay_msg = "❌ Sheet ထဲတွင် Payment အချက်အလက် မရှိသေးပါ။"
        except Exception:
            pay_msg = "❌ Payment info ရယူရာတွင် အမှားအယွင်းရှိနေပါသည်။"
        
        await query.edit_message_text(pay_msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data='payment_list')]]), parse_mode="Markdown")

    elif query.data == 'main_services':
        buttons = [[InlineKeyboardButton("Advertising Service About", callback_data='about')],
                   [InlineKeyboardButton("User Info", callback_data='user_info')],
                   [InlineKeyboardButton("Payment Method", callback_data='payment_list')]]
        await query.edit_message_text("ဝန်ဆောင်မှုများ ရယူရန် ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        admin_id = get_admin_id()
        if not admin_id:
            await update.message.reply_text("❌ Admin မသတ်မှတ်ရသေးပါ။")
            return

        user = update.effective_user
        caption = f"📩 **New Payment Receipt**\nFrom: {user.first_name}\nID: `{user.id}`\n\nMember ပေးရန် 'user' sheet တွင် 'Member' ဟု ရေးပေးပါ။"
        await context.bot.send_photo(chat_id=admin_id, photo=update.message.photo[-1].file_id, caption=caption, parse_mode="Markdown")
        await update.message.reply_text("✅ ပြေစာကို Admin ထံ ပို့လိုက်ပါပြီ။")

# --- Startup ---
def main():
    # Web Port Scan ကို ကျော်ဖြတ်ရန် Flask Server ကို သီးခြား Thread ဖြင့် run သည်
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    
    # drop_pending_updates=True ထည့်ခြင်းဖြင့် Conflict Error ကို ဖြေရှင်းသည်
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
