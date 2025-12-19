# Meow Advertising Service Bot

Telegram bot for advertising services with Google Sheets integration.

## Features
- User level management (Gold, Platinum, Ruby)
- Payment processing
- Admin approval system
- Google Sheets integration for data storage

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token
- Google Cloud Service Account
- Google Sheets with proper sheets

### 2. Environment Variables
Create a `.env` file with:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_SHEET_KEY=your_google_service_account_json
SHEET_ID=your_google_sheet_id
ADMIN_IDS=admin_telegram_id1,admin_telegram_id2
WEBHOOK_URL=https://your-app.onrender.com
PORT=5000
