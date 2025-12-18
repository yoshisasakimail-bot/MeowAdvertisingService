import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from google_sheets import GoogleSheetsHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Initialize Google Sheets
gsheets = GoogleSheetsHandler()

# Store user states
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with advertising service button"""
    user = update.effective_user
    
    welcome_text = f"""
👋 ကြိုဆိုပါတယ် {user.first_name}!

ကျွန်ုပ်တို့၏ ဝန်ဆောင်မှုများကို ရယူလိုပါက အောက်ပါခလုပ်ကို နှိပ်ပါ။
    """
    
    # Create keyboard with advertising service button
    keyboard = [
        [KeyboardButton("🚀 AdvertisingService")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text
    
    if text == "🚀 AdvertisingService":
        # Check if user has access
        user_id = update.effective_user.id
        
        if gsheets.check_user_access(user_id):
            await show_advertising_menu(update, context)
        else:
            await update.message.reply_text(
                "⚠️ ဝန်ဆောင်မှုရယူရန် အကောင့်ဖွင့်ရန်လိုအပ်ပါသည်။\n\n"
                "ကျေးဇူးပြု၍ အောက်ပါအဆင့်များကို လိုက်နာပါ:\n"
                "1. ငွေလွှဲရန် - 09XXXXXXXXX (Admin Name)\n"
                "2. လွှဲပြီးသော Screenshot ကို Admin ထံပေးပို့ပါ\n"
                "3. Admin မှ သင့်အကောင့်ကို ဖွင့်ပေးပါမည်"
            )
    
    elif text == "Back to Main":
        await start(update, context)

async def show_advertising_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show advertising service menu with 7 buttons"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Advertising Lv.1", callback_data="adv_lv1"),
            InlineKeyboardButton("📈 Advertising Lv.2", callback_data="adv_lv2")
        ],
        [
            InlineKeyboardButton("🚀 Advertising Lv.3", callback_data="adv_lv3"),
            InlineKeyboardButton("ℹ️ Advertising Info", callback_data="adv_info")
        ],
        [
            InlineKeyboardButton("❓ Help Center", callback_data="help"),
            InlineKeyboardButton("💳 Payment Method", callback_data="payment")
        ],
        [
            InlineKeyboardButton("🔚 Cut off", callback_data="cutoff")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 AdvertisingService Menu\n\n"
        "အောက်ပါ ဝန်ဆောင်မှုများမှ ရွေးချယ်နိုင်ပါသည်:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Back button for each service
    back_button = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]
    
    if data == "adv_lv1":
        await query.edit_message_text(
            text="📊 Advertising Level 1\n\n"
                 "အဆင့် 1 ကြော်ငြာဝန်ဆောင်မှု အသေးစိတ်\n"
                 "💰 ဈေးနှုန်း: 10,000 MMK\n"
                 "⏰ ကြာချိန်: 7 ရက်\n"
                 "✅ ဝန်ဆောင်မှုများ:\n"
                 "- Facebook Post\n"
                 "- Telegram Channel\n"
                 "- Basic Design",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "adv_lv2":
        await query.edit_message_text(
            text="📈 Advertising Level 2\n\n"
                 "အဆင့် 2 ကြော်ငြာဝန်ဆောင်မှု အသေးစိတ်\n"
                 "💰 ဈေးနှုန်း: 20,000 MMK\n"
                 "⏰ ကြာချိန်: 14 ရက်\n"
                 "✅ ဝန်ဆောင်မှုများ:\n"
                 "- Facebook + Instagram\n"
                 "- Telegram Groups\n"
                 "- Professional Design",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "adv_lv3":
        await query.edit_message_text(
            text="🚀 Advertising Level 3\n\n"
                 "အဆင့် 3 ကြော်ငြာဝန်ဆောင်မှု အသေးစိတ်\n"
                 "💰 ဈေးနှုန်း: 35,000 MMK\n"
                 "⏰ ကြာချိန်: 30 ရက်\n"
                 "✅ ဝန်ဆောင်မှုများ:\n"
                 "- All Social Media\n"
                 "- Video Promotion\n"
                 "- Premium Design\n"
                 "- Analytics Report",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "adv_info":
        await query.edit_message_text(
            text="ℹ️ Advertising Information\n\n"
                 "ကြော်ငြာဝန်ဆောင်မှုဆိုင်ရာ အချက်အလက်များ:\n\n"
                 "📞 Contact: 09XXXXXXXXX\n"
                 "🕒 Working Hours: 9AM - 6PM\n"
                 "📧 Email: admin@example.com\n"
                 "📍 Location: Yangon, Myanmar",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "help":
        await query.edit_message_text(
            text="❓ Help Center\n\n"
                 "အကူအညီလိုအပ်ပါက:\n\n"
                 "1. ငွေလွှဲပြဿနာများ\n"
                 "2. ဝန်ဆောင်မှုပြဿနာများ\n"
                 "3. အကောင့်ပြဿနာများ\n\n"
                 "Admin သို့ တိုက်ရိုက်ဆက်သွယ်ပါ။",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "payment":
        await query.edit_message_text(
            text="💳 Payment Methods\n\n"
                 "လက်ခံသော ငွေလွှဲနည်းများ:\n\n"
                 "1. KBZ Pay\n"
                 "2. Wave Money\n"
                 "3. CB Bank\n"
                 "4. AYA Bank\n"
                 "5. Cash (Yangon Only)\n\n"
                 "Admin: 09XXXXXXXXX",
            reply_markup=InlineKeyboardMarkup(back_button)
        )
    
    elif data == "cutoff":
        await query.edit_message_text(
            text="🔚 အသုံးပြုမှုပြီးဆုံးပါပြီ။\n\n"
                 "နောက်တစ်ကြိမ်ထပ်မံအသုံးပြုလိုပါက /start ကိုနှိပ်ပါ။"
        )
    
    elif data == "back_to_menu":
        await show_advertising_menu_from_query(query, context)

async def show_advertising_menu_from_query(query, context):
    """Show menu from callback query"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Advertising Lv.1", callback_data="adv_lv1"),
            InlineKeyboardButton("📈 Advertising Lv.2", callback_data="adv_lv2")
        ],
        [
            InlineKeyboardButton("🚀 Advertising Lv.3", callback_data="adv_lv3"),
            InlineKeyboardButton("ℹ️ Advertising Info", callback_data="adv_info")
        ],
        [
            InlineKeyboardButton("❓ Help Center", callback_data="help"),
            InlineKeyboardButton("💳 Payment Method", callback_data="payment")
        ],
        [
            InlineKeyboardButton("🔚 Cut off", callback_data="cutoff")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🎯 AdvertisingService Menu\n\n"
        "အောက်ပါ ဝန်ဆောင်မှုများမှ ရွေးချယ်နိုင်ပါသည်:",
        reply_markup=reply_markup
    )

def main():
    """Start the bot"""
    # Get bot token from environment
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
