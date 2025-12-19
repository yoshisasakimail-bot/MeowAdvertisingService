import logging
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from flask import Flask, request
import threading
from config import Config

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app for webhooks
app = Flask(__name__)

# Initialize Google Sheets
def init_google_sheets():
    try:
        # Parse the Google Sheet key JSON
        sheet_key_json = json.loads(Config.GOOGLE_SHEET_KEY)
        
        scope = ["https://spreadsheets.google.com/feeds", 
                "https://www.googleapis.com/auth/drive"]
        
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            sheet_key_json, scope
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(Config.SHEET_ID)
        return sheet
    except Exception as e:
        logger.error(f"Error initializing Google Sheets: {e}")
        return None

# Global sheet variable
sheet = init_google_sheets()

# Store user levels in memory (you can also use Google Sheets)
user_levels = {}

# Google Sheets Helper Functions
def get_about_info():
    """Get about information from Google Sheets"""
    try:
        if sheet:
            about_sheet = sheet.worksheet(Config.ABOUT_SHEET_NAME)
            return about_sheet.get_all_values()
    except Exception as e:
        logger.error(f"Error getting about info: {e}")
    return [["About information not found"]]

def get_payment_methods():
    """Get payment methods and prices from Google Sheets"""
    try:
        if sheet:
            payment_sheet = sheet.worksheet(Config.PAYMENTS_SHEET_NAME)
            return payment_sheet.get_all_values()
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
    return [["Payment methods not found"]]

def update_user_level(user_id, username, name, level):
    """Update user level in Google Sheets"""
    try:
        if sheet:
            users_sheet = sheet.worksheet(Config.USERS_SHEET_NAME)
            
            # Check if user exists
            try:
                cell = users_sheet.find(str(user_id))
                users_sheet.update_cell(cell.row, 5, level)  # Update level
            except gspread.exceptions.CellNotFound:
                # Add new user
                users_sheet.append_row([
                    str(user_id),
                    username,
                    name,
                    str(int(time.time())),
                    level
                ])
            
            # Update in-memory cache
            user_levels[user_id] = level
            return True
    except Exception as e:
        logger.error(f"Error updating user level: {e}")
    return False

def get_user_info(user_id):
    """Get user information from Google Sheets"""
    try:
        if sheet:
            users_sheet = sheet.worksheet(Config.USERS_SHEET_NAME)
            cell = users_sheet.find(str(user_id))
            if cell:
                user_data = users_sheet.row_values(cell.row)
                return {
                    'level': user_data[4] if len(user_data) > 4 else 'None',
                    'user_id': user_data[0],
                    'name': user_data[2],
                    'username': user_data[1]
                }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
    
    # Return default if not found
    return {
        'level': 'None',
        'user_id': user_id,
        'name': 'User',
        'username': 'Not set'
    }

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    welcome_message = (
        f"{user.first_name} MeowAdvertisingServiceBot မှ ကြိုဆိုပါတယ်။\n\n"
        "MeowAdvertisingService ၀န်ဆောင်မူများရယူရန် /service ကိုနိပ်ပါ။"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=ReplyKeyboardRemove()
    )

async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /service command - Show service menu"""
    keyboard = [
        [
            InlineKeyboardButton("1. Advertising About", callback_data="about"),
            InlineKeyboardButton("2. User Info", callback_data="user_info")
        ],
        [
            InlineKeyboardButton("3. Payment Method", callback_data="payment")
        ],
        [
            InlineKeyboardButton("4. Close Menu", callback_data="close_menu")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "Meow Advertising Service Menu:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            "Meow Advertising Service Menu:",
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "about":
        await show_about(update, context)
    elif data == "user_info":
        await show_user_info(update, context)
    elif data == "payment":
        await show_payment_methods(update, context)
    elif data == "close_menu":
        await close_menu(update, context)
    elif data.startswith("pay_"):
        await show_payment_options(update, context, data)
    elif data.startswith("method_"):
        await request_payment_screenshot(update, context, data)
    elif data == "back_to_service":
        await service_menu(update, context)
    elif data == "back_to_payment":
        await show_payment_methods(update, context)

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show advertising about information"""
    about_data = get_about_info()
    about_text = "Advertising About:\n\n"
    
    for row in about_data:
        about_text += "\n".join(row) + "\n\n"
    
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="back_to_service")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        about_text,
        reply_markup=reply_markup
    )

async def show_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user information"""
    user_id = update.callback_query.from_user.id
    user_info = get_user_info(user_id)
    
    user_text = (
        f"User Level - {user_info['level']}\n"
        f"User ID - {user_info['user_id']}\n"
        f"Name - {user_info['name']}\n"
        f"User name - @{user_info['username']}\n\n"
        "Level အကြောင်းရာကို payment method မှာ ရေးပေးမယ်"
    )
    
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="back_to_service")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        user_text,
        reply_markup=reply_markup
    )

async def show_payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment methods"""
    payment_data = get_payment_methods()
    
    # Create buttons for each payment plan
    keyboard = []
    
    # Skip header row if exists
    start_index = 1 if len(payment_data) > 1 and "Plan" in payment_data[0][0] else 0
    
    for i, row in enumerate(payment_data[start_index:], start=1):
        if row and row[0]:  # Check if row has data
            plan_name = row[0]
            keyboard.append([
                InlineKeyboardButton(f"{i}. {plan_name}", callback_data=f"pay_{plan_name}")
            ])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="back_to_service")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Format payment methods text
    payment_text = "Payment Method:\n\n"
    for row in payment_data:
        if row:  # Check if row is not empty
            payment_text += " | ".join([str(item) for item in row if item]) + "\n"
    
    await update.callback_query.edit_message_text(
        payment_text,
        reply_markup=reply_markup
    )

async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment options after selecting a plan"""
    plan_name = update.callback_query.data.replace("pay_", "")
    
    context.user_data['selected_plan'] = plan_name
    
    keyboard = [
        [
            InlineKeyboardButton("KBZ Payment", callback_data=f"method_KBZ_{plan_name}"),
            InlineKeyboardButton("Wave Money", callback_data=f"method_Wave_{plan_name}")
        ],
        [InlineKeyboardButton("Back", callback_data="back_to_payment")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"၀ယ်ယူအူဆိုင်ရာ: {plan_name}\n\n"
        "ကျေးဇူးပြု၍ ငွေပေးချေမှုနည်းလမ်းရွေးချယ်ပါ:",
        reply_markup=reply_markup
    )

async def request_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Request payment screenshot from user"""
    data_parts = update.callback_query.data.split("_")
    method = data_parts[1]
    plan = "_".join(data_parts[2:]) if len(data_parts) > 2 else ""
    
    context.user_data['payment_method'] = method
    context.user_data['selected_plan'] = plan
    
    await update.callback_query.edit_message_text(
        f"ကျေးဇူးပြု၍ {method} ဖြင့် ငွေပေးချေပြီး screen shot ပေးပို့ရန်။\n\n"
        f"Plan: {plan}\n"
        f"Payment Method: {method}"
    )
    
    # Store payment request info for photo handling
    context.user_data['awaiting_screenshot'] = True

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment screenshot from user"""
    if context.user_data.get('awaiting_screenshot'):
        user = update.effective_user
        photo = update.message.photo[-1]  # Get highest resolution photo
        
        # Forward to all admins
        for admin_id in Config.ADMIN_IDS:
            try:
                # Send photo with admin buttons
                keyboard = [
                    [
                        InlineKeyboardButton("Gold", callback_data=f"admin_approve_{user.id}_Gold"),
                        InlineKeyboardButton("Platinum", callback_data=f"admin_approve_{user.id}_Platinum"),
                        InlineKeyboardButton("Ruby", callback_data=f"admin_approve_{user.id}_Ruby")
                    ],
                    [InlineKeyboardButton("Failed", callback_data=f"admin_reject_{user.id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                caption = (
                    f"Payment Screenshot from:\n"
                    f"User: {user.first_name}\n"
                    f"ID: {user.id}\n"
                    f"Username: @{user.username}\n"
                    f"Plan: {context.user_data.get('selected_plan', 'N/A')}\n"
                    f"Method: {context.user_data.get('payment_method', 'N/A')}"
                )
                
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=photo.file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error sending to admin {admin_id}: {e}")
        
        await update.message.reply_text(
            "ကျေးဇူးတင်ပါသည်။ သင်၏ screen shot ကို admin ထံပေးပို့ပြီးပါပြီ။ "
            "အတည်ပြုပြီးနောက် သင့်အဆင့်ကို အပ်ဒိတ်လုပ်ပေးပါမည်။"
        )
        
        # Reset the flag
        context.user_data['awaiting_screenshot'] = False

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callbacks for approving/rejecting payments"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    admin_id = query.from_user.id
    
    # Check if user is admin
    if admin_id not in Config.ADMIN_IDS:
        await query.edit_message_text("Unauthorized action.")
        return
    
    if data.startswith("admin_approve_"):
        # Format: admin_approve_USERID_LEVEL
        parts = data.split("_")
        if len(parts) >= 4:
            user_id = int(parts[2])
            level = parts[3]
            
            # Update user level
            user = await context.bot.get_chat(user_id)
            success = update_user_level(
                user_id=user_id,
                username=user.username or "N/A",
                name=user.first_name or "User",
                level=level
            )
            
            if success:
                # Notify user
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🎉 ကျေးဇူးတင်ပါသည်။\n\n"
                        f"သင်၏ Level ကို {level} အဖြစ် အတည်ပြုပြီးပါပြီ။\n"
                        f"ယခု {level} ၀န်ဆောင်မှုများကို အသုံးပြုနိုင်ပါပြီ။"
                    ),
                    reply_markup=get_level_keyboard(level)
                )
                
                # Update admin message
                await query.edit_message_text(
                    f"✅ Approved! User {user_id} is now {level} level.",
                    reply_markup=None
                )
            else:
                await query.edit_message_text("❌ Error updating user level.")
    
    elif data.startswith("admin_reject_"):
        # Format: admin_reject_USERID
        parts = data.split("_")
        if len(parts) >= 3:
            user_id = int(parts[2])
            
            # Notify user
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ သင်၏ payment အား အတည်မပြုနိုင်ပါ။ ကျေးဇူးပြု၍ ထပ်မံကြိုးစားပါ။"
            )
            
            # Update admin message
            await query.edit_message_text(
                f"❌ Rejected! User {user_id} payment rejected.",
                reply_markup=None
            )

def get_level_keyboard(level):
    """Get reply keyboard for specific level"""
    if level == "Gold":
        keyboard = [["Gold Services"]]
    elif level == "Platinum":
        keyboard = [["Platinum Services"]]
    elif level == "Ruby":
        keyboard = [["Ruby Services"]]
    else:
        keyboard = [["No Services Available"]]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close service menu"""
    await update.callback_query.edit_message_text(
        "Service Menu: off\n\n"
        "MeowAdvertisingService ၀န်ဆောင်မူများရယူရန် /service ကိုနိပ်ပါ။",
        reply_markup=None
    )

async def level_service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle level-specific service buttons"""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Get user level
    user_info = get_user_info(user_id)
    user_level = user_info['level']
    
    if text == "Gold Services" and user_level == "Gold":
        await update.message.reply_text(
            "Gold Level Services:\n\n"
            "1. Service 1\n"
            "2. Service 2\n"
            "3. Service 3\n\n"
            "More features for Gold members..."
        )
    elif text == "Platinum Services" and user_level == "Platinum":
        await update.message.reply_text(
            "Platinum Level Services:\n\n"
            "1. Service 1\n"
            "2. Service 2\n"
            "3. Service 3\n"
            "4. Service 4\n\n"
            "Premium features for Platinum members..."
        )
    elif text == "Ruby Services" and user_level == "Ruby":
        await update.message.reply_text(
            "Ruby Level Services:\n\n"
            "1. Service 1\n"
            "2. Service 2\n"
            "3. Service 3\n"
            "4. Service 4\n"
            "5. Service 5\n\n"
            "VIP features for Ruby members..."
        )
    else:
        await update.message.reply_text(
            "You don't have access to this service. Please upgrade your level.",
            reply_markup=ReplyKeyboardRemove()
        )

# Flask routes for webhook
@app.route('/')
def index():
    return "Meow Advertising Service Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming updates from Telegram"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return 'OK'

def run_flask():
    """Run Flask server for webhook"""
    app.run(host='0.0.0.0', port=Config.PORT)

def main():
    """Start the bot"""
    # Create Application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("service", service_menu))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, level_service_handler))
    
    # Set up webhook if WEBHOOK_URL is configured
    if Config.WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=Config.PORT,
            url_path="webhook",
            webhook_url=f"{Config.WEBHOOK_URL}/webhook"
        )
    else:
        # Run with polling (for development)
        print("Starting bot with polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
