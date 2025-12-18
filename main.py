import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
GOOGLE_SHEET_NAME = "Your_Sheet_Name"
JSON_KEYFILE = "service_account.json" # Google Service Account JSON file

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_KEYFILE, scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

# --- Handlers ---
async def start(update: update, context: ContextTypes.DEFAULT_TYPE):
    # Reply Keyboard with "Advertising Service"
    keyboard = [["Advertising Service"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome! Please select a service below:",
        reply_markup=reply_markup
    )

async def handle_message(update: update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "Advertising Service":
        # Save User Info to Google Sheet
        user = update.effective_user
        sheet.append_row([user.id, user.first_name, user.username])
        
        # Inline Buttons
        buttons = [
            [InlineKeyboardButton("Advertising Info", callback_data='info')],
            [InlineKeyboardButton("Advertising Setting", callback_data='setting')],
            [InlineKeyboardButton("Users Info", callback_data='users')],
            [InlineKeyboardButton("Payment Method", callback_data='payment')],
            [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Our Services:", reply_markup=reply_markup)

async def button_click(update: update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    back_button = [[InlineKeyboardButton("Back", callback_data='back_to_services')]]
    reply_markup = InlineKeyboardMarkup(back_button)

    if query.data == 'info':
        await query.edit_message_text("This is Advertising Info section.", reply_markup=reply_markup)
    elif query.data == 'setting':
        await query.edit_message_text("This is Advertising Setting section.", reply_markup=reply_markup)
    elif query.data == 'users':
        await query.edit_message_text("This is Users Info section.", reply_markup=reply_markup)
    elif query.data == 'payment':
        await query.edit_message_text("This is Payment Method section.", reply_markup=reply_markup)
    elif query.data == 'back_to_menu':
        await query.message.reply_text("Main Menu", reply_markup=ReplyKeyboardMarkup([["Advertising Service"]], resize_keyboard=True))
    elif query.data == 'back_to_services':
        # Return to the 5 buttons
        buttons = [
            [InlineKeyboardButton("Advertising Info", callback_data='info')],
            [InlineKeyboardButton("Advertising Setting", callback_data='setting')],
            [InlineKeyboardButton("Users Info", callback_data='users')],
            [InlineKeyboardButton("Payment Method", callback_data='payment')],
            [InlineKeyboardButton("Back to Menu", callback_data='back_to_menu')]
        ]
        await query.edit_message_text("Our Services:", reply_markup=InlineKeyboardMarkup(buttons))

# --- Main Function ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
