from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    ConversationHandler,
    filters
)
import logging
from datetime import datetime
import json
import asyncio

from config import Config
from google_sheets import GoogleSheetsManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# States for ConversationHandler
SELECTING_SERVICE, CHOOSING_PLAN, PAYMENT_METHOD, UPLOAD_PROOF = range(4)

# Initialize Google Sheets
sheets_manager = GoogleSheetsManager()

# ========== KEYBOARDS ==========

def get_main_keyboard(user_id):
    """Check if user has access and return appropriate keyboard"""
    has_access = sheets_manager.check_user_access(user_id)
    
    if has_access:
        # If user has paid and approved
        keyboard = [
            [KeyboardButton("Advertising Lv.1"), KeyboardButton("Advertising Lv.2")],
            [KeyboardButton("Advertising Lv.3"), KeyboardButton("Advertising Info")],
            [KeyboardButton("Help Center"), KeyboardButton("Payment Method")],
            [KeyboardButton("Cut Off")]
        ]
    else:
        # If user hasn't paid yet
        keyboard = [
            [KeyboardButton("Advertising Service")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_keyboard():
    """Keyboard with Back button"""
    keyboard = [[KeyboardButton("⬅️ Back")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """Admin keyboard"""
    keyboard = [
        [KeyboardButton("👥 View Users"), KeyboardButton("✅ Approve Payment")],
        [KeyboardButton("📊 Statistics"), KeyboardButton("📢 Broadcast")],
        [KeyboardButton("⬅️ Main Menu")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ========== COMMAND HANDLERS ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.message.from_user
    user_id = user.id
    
    welcome_message = """
    🎉 *Welcome to Advertising Service Bot!* 🎉

    ကျွန်ုပ်တို့၏ advertising services များကို ရယူလိုပါက 
    "Advertising Service" ခလုတ်ကို နှိပ်ပါ။

    ဝန်ဆောင်မှုများအကြောင်း အသေးစိတ်သိရှိလိုပါက 
    "Help Center" ခလုတ်ကို နှိပ်ပါ။

    📞 Contact Admin: @admin_username
    """
    
    # Send welcome message with main keyboard
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard(user_id)
    )
    
    # Log user
    log_user_activity(user)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
    *🤖 Bot Commands:*
    /start - Start the bot
    /help - Show this help message
    /about - About this bot
    
    *📱 Services Available:*
    1. Advertising Lv.1 - 7 days
    2. Advertising Lv.2 - 14 days  
    3. Advertising Lv.3 - 30 days
    
    *💳 Payment Methods:*
    • KBZ Pay
    • Wave Pay
    • Aya Pay
    • CB Pay
    
    *🆘 Need Help?*
    Contact: @admin_username
    """
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

# ========== SERVICE FLOW ==========

async def advertising_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Advertising Service button"""
    user_id = update.message.from_user.id
    
    # Check if user already has access
    if sheets_manager.check_user_access(user_id):
        await update.message.reply_text(
            "✅ You already have access to our services!",
            reply_markup=get_main_keyboard(user_id)
        )
        return
    
    # Start service selection
    service_menu = """
    *🎯 Advertising Service Plans*

    Please choose your plan:
    
    *Level 1 - 10,000 MMK*
    • Duration: 7 days
    • Basic features
    • Standard support
    
    *Level 2 - 20,000 MMK*
    • Duration: 14 days
    • Advanced features
    • Priority support
    
    *Level 3 - 30,000 MMK*
    • Duration: 30 days
    • All features
    • VIP support
    
    Choose a level to proceed:
    """
    
    keyboard = [
        [KeyboardButton("Advertising Lv.1"), KeyboardButton("Advertising Lv.2")],
        [KeyboardButton("Advertising Lv.3"), KeyboardButton("⬅️ Back")]
    ]
    
    await update.message.reply_text(
        service_menu,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return SELECTING_SERVICE

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan selection"""
    plan_text = update.message.text
    user = update.message.from_user
    
    # Map plan names to keys
    plan_map = {
        "Advertising Lv.1": "level1",
        "Advertising Lv.2": "level2", 
        "Advertising Lv.3": "level3"
    }
    
    if plan_text not in plan_map:
        await update.message.reply_text(
            "Please select a valid plan.",
            reply_markup=get_back_keyboard()
        )
        return SELECTING_SERVICE
    
    plan_key = plan_map[plan_text]
    plan = Config.SERVICE_PLANS[plan_key]
    
    # Store selected plan in context
    context.user_data['selected_plan'] = plan_key
    
    # Show plan details and ask for confirmation
    plan_details = f"""
    *📋 Plan Details: {plan['name']}*
    
    💰 Price: {plan['price']}
    📅 Duration: {plan['duration']}
    
    *✨ Features:*
    {chr(10).join(['• ' + feature for feature in plan['features']])}
    
    Do you want to proceed with this plan?
    """
    
    keyboard = [
        [KeyboardButton("✅ Confirm"), KeyboardButton("❌ Cancel")]
    ]
    
    await update.message.reply_text(
        plan_details,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return CHOOSING_PLAN

async def confirm_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plan confirmation"""
    if update.message.text == "❌ Cancel":
        await update.message.reply_text(
            "Plan selection cancelled.",
            reply_markup=get_main_keyboard(update.message.from_user.id)
        )
        return ConversationHandler.END
    
    # Show payment methods
    payment_methods = """
    *💳 Select Payment Method*
    
    Please choose your preferred payment method:
    
    1. KBZ Pay
    2. Wave Pay  
    3. Aya Pay
    4. CB Pay
    
    After payment, you'll need to upload proof.
    """
    
    keyboard = [
        [KeyboardButton("KBZ Pay"), KeyboardButton("Wave Pay")],
        [KeyboardButton("Aya Pay"), KeyboardButton("CB Pay")],
        [KeyboardButton("⬅️ Back")]
    ]
    
    await update.message.reply_text(
        payment_methods,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return PAYMENT_METHOD

async def select_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection"""
    method = update.message.text
    
    if method == "⬅️ Back":
        # Go back to plan selection
        return await advertising_service(update, context)
    
    # Store payment method
    context.user_data['payment_method'] = method
    
    # Get account number based on method
    account_number = Config.PAYMENT_METHODS.get(
        method.lower().replace(" ", "_"),
        "09XXXXXXXX"
    )
    
    payment_instructions = f"""
    *💰 Payment Instructions*
    
    Please send payment to:
    
    Method: {method}
    Account: {account_number}
    
    *Amount:* {Config.SERVICE_PLANS[context.user_data['selected_plan']]['price']}
    
    *Important:*
    1. Send exact amount
    2. Keep transaction screenshot
    3. Upload proof after payment
    
    After payment, upload screenshot as photo.
    """
    
    await update.message.reply_text(
        payment_instructions,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )
    
    return UPLOAD_PROOF

async def handle_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment proof upload"""
    user = update.message.from_user
    
    if update.message.photo:
        # Get the largest photo
        photo = update.message.photo[-1]
        
        # Store photo file_id
        context.user_data['payment_proof'] = photo.file_id
        
        # Save to Google Sheets
        user_data = {
            'user_id': user.id,
            'username': user.username or user.first_name,
            'first_name': user.first_name,
            'plan': context.user_data['selected_plan'],
            'amount': Config.SERVICE_PLANS[context.user_data['selected_plan']]['price'],
            'payment_method': context.user_data['payment_method'],
            'payment_proof': photo.file_id,
            'status': 'pending',
            'joined_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'expiry_date': ''  # Will be set after approval
        }
        
        # Add to Google Sheets
        success = sheets_manager.add_user(user_data)
        
        if success:
            # Notify admin
            await notify_admin(user, user_data, photo.file_id)
            
            # Send confirmation to user
            confirmation = """
            *✅ Payment Proof Received!*
            
            Your payment proof has been submitted successfully.
            
            *Next Steps:*
            1. Admin will verify your payment
            2. You'll receive notification when approved
            3. Access will be granted within 24 hours
            
            Status: ⏳ Pending Approval
            
            Thank you for your patience!
            """
            
            await update.message.reply_text(
                confirmation,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(user.id)
            )
        else:
            await update.message.reply_text(
                "❌ Error saving your information. Please contact admin.",
                reply_markup=get_main_keyboard(user.id)
            )
        
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            "Please upload a photo/screenshot of your payment proof.",
            reply_markup=get_back_keyboard()
        )
        return UPLOAD_PROOF

async def notify_admin(user, user_data, proof_file_id):
    """Notify admin about new payment"""
    admin_message = f"""
    *🆕 New Payment Submission*
    
    👤 User: {user_data['first_name']} (@{user_data['username']})
    🆔 ID: {user_data['user_id']}
    📋 Plan: {user_data['plan']}
    💰 Amount: {user_data['amount']}
    💳 Method: {user_data['payment_method']}
    📅 Date: {user_data['joined_date']}
    
    Payment proof attached.
    """
    
    # Send to all admins
    for admin_id in Config.ADMIN_IDS:
        try:
            # Send message
            # Note: You'll need to pass application context here
            # This is a simplified version
            pass
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")

# ========== OTHER MENU ITEMS ==========

async def advertising_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show advertising information"""
    info_text = """
    *📊 Advertising Information*
    
    *Why Choose Us?*
    • Targeted audience reach
    • High engagement rates
    • Affordable pricing
    • 24/7 support
    
    *📈 Results You Can Expect:*
    • Increased visibility
    • More customers
    • Higher sales
    • Brand recognition
    
    *🕐 Processing Time:*
    • Approval: Within 24 hours
    • Setup: Within 48 hours
    
    Contact for custom packages!
    """
    
    await update.message.reply_text(
        info_text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def help_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help center"""
    help_text = """
    *🆘 Help Center*
    
    *Frequently Asked Questions:*
    
    *Q: How long does approval take?*
    A: Usually within 24 hours.
    
    *Q: What if my payment fails?*
    A: Contact admin with transaction details.
    
    *Q: Can I upgrade my plan?*
    A: Yes, contact admin for upgrade options.
    
    *Q: How to cancel service?*
    A: Contact admin 3 days before expiry.
    
    *📞 Contact Support:*
    • Email: support@example.com
    • Telegram: @admin_username
    • Hours: 9AM - 6PM (MMT)
    """
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment methods"""
    methods_text = """
    *💳 Available Payment Methods*
    
    *1. KBZ Pay*
    Account: 09XXXXXXXX
    Name: John Doe
    
    *2. Wave Pay*
    Account: 09XXXXXXXX  
    Name: John Doe
    
    *3. Aya Pay*
    Account: 09XXXXXXXX
    Name: John Doe
    
    *4. CB Pay*
    Account: 09XXXXXXXX
    Name: John Doe
    
    *📝 Important Notes:*
    • Send exact amount
    • Include user ID in remark
    • Save transaction screenshot
    • Upload proof immediately
    """
    
    await update.message.reply_text(
        methods_text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def cut_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cut off button"""
    # This would typically check user's remaining days
    # For now, show a simple message
    
    cut_off_text = """
    *⏰ Service Cut Off*
    
    Your service will expire in: 7 days
    
    *To renew:*
    1. Contact admin
    2. Make payment
    3. Upload proof
    
    *Early renewal bonus:*
    Get 2 extra days for early renewal!
    """
    
    await update.message.reply_text(
        cut_off_text,
        parse_mode='Markdown',
        reply_markup=get_back_keyboard()
    )

async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button"""
    user_id = update.message.from_user.id
    await update.message.reply_text(
        "Returning to main menu...",
        reply_markup=get_main_keyboard(user_id)
    )
    return ConversationHandler.END

# ========== ADMIN FUNCTIONS ==========

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel"""
    user_id = update.message.from_user.id
    
    if user_id not in Config.ADMIN_IDS:
        await update.message.reply_text("Unauthorized access!")
        return
    
    admin_text = """
    *👑 Admin Panel*
    
    Available Commands:
    
    • View all users
    • Approve payments
    • Check statistics
    • Send broadcast messages
    
    Select an option:
    """
    
    await update.message.reply_text(
        admin_text,
        parse_mode='Markdown',
        reply_markup=get_admin_keyboard()
    )

# ========== UTILITY FUNCTIONS ==========

def log_user_activity(user):
    """Log user activity"""
    print(f"[{datetime.now()}] User {user.id} ({user.first_name}) started bot")

# ========== MAIN FUNCTION ==========

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Conversation handler for service flow
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Advertising Service$"), advertising_service)
        ],
        states={
            SELECTING_SERVICE: [
                MessageHandler(filters.Regex("^(Advertising Lv\.1|Advertising Lv\.2|Advertising Lv\.3)$"), select_plan),
                MessageHandler(filters.Regex("^⬅️ Back$"), back_button)
            ],
            CHOOSING_PLAN: [
                MessageHandler(filters.Regex("^(✅ Confirm|❌ Cancel)$"), confirm_plan)
            ],
            PAYMENT_METHOD: [
                MessageHandler(filters.Regex("^(KBZ Pay|Wave Pay|Aya Pay|CB Pay)$"), select_payment_method),
                MessageHandler(filters.Regex("^⬅️ Back$"), advertising_service)
            ],
            UPLOAD_PROOF: [
                MessageHandler(filters.PHOTO, handle_payment_proof),
                MessageHandler(filters.Regex("^⬅️ Back$"), advertising_service)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", back_button),
            MessageHandler(filters.Regex("^Cancel$"), back_button)
        ]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    
    # Other menu handlers
    application.add_handler(MessageHandler(filters.Regex("^Advertising Info$"), advertising_info))
    application.add_handler(MessageHandler(filters.Regex("^Help Center$"), help_center))
    application.add_handler(MessageHandler(filters.Regex("^Payment Method$"), payment_method))
    application.add_handler(MessageHandler(filters.Regex("^Cut Off$"), cut_off))
    application.add_handler(MessageHandler(filters.Regex("^⬅️ Back$"), back_button))
    
    # Admin command
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Start the bot
    print("🤖 Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
