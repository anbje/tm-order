"""
Telegram bot for Translation Order Management
Handles mini-app integration and deadline reminders
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import requests
import schedule
import time
from threading import Thread

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://api:8000")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "https://localhost/bot/webhook")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    await update.message.reply_text(
        "Welcome to TM-Order! 📋\n\n"
        "Your translation management system is running.\n\n"
        "🌐 Web UI: https://localhost\n"
        "📅 Calendar: https://localhost/calendar/ics?token=rama_tm_secret_2025\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/done - Mark order as delivered\n"
        "/help - Show help\n\n"
        "💡 Use the web interface to create and manage orders."
    )

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark order as delivered"""
    # TODO: Extract order ID from context and update via API
    await update.message.reply_text("✅ Order marked as delivered!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    await update.message.reply_text(
        "📋 **TM-Order Help**\n\n"
        "This bot provides deadline reminders for your translation orders.\n\n"
        "**Available Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/done - Mark order as delivered\n\n"
        "**How to use:**\n"
        "1. Create orders via web UI: https://localhost\n"
        "2. Bot will send reminder 24h before deadline\n"
        "3. Use /done to mark as completed\n\n"
        "📅 Subscribe to calendar feed:\n"
        "https://localhost/calendar/ics?token=rama_tm_secret_2025"
    )

def check_reminders():
    """Background job to check for upcoming deadlines"""
    try:
        response = requests.get(f"{API_URL}/api/orders/check-reminders")
        if response.status_code == 200:
            orders = response.json()
            for order in orders:
                # TODO: Send reminder message to user
                logger.info(f"Reminder needed for order #{order['id']}")
                # Mark as sent
                requests.post(f"{API_URL}/api/orders/{order['id']}/mark-reminder-sent")
    except Exception as e:
        logger.error(f"Error checking reminders: {e}")

def run_scheduler():
    """Run background scheduler in separate thread"""
    schedule.every(15).minutes.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    """Start the bot"""
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("done", done))
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Bot started")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
