"""
Telegram bot for Translation Order Management
Handles mini-app integration and deadline reminders
"""
import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters, TypeHandler
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

# Conversation states
ORDER_CUSTOMER, ORDER_TOPIC, ORDER_DEADLINE, ORDER_SRC_LANG, ORDER_TGT_LANG, ORDER_WORDS = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    logging.info("/start command received")
    await update.message.reply_text(
        "Welcome to TM-Order! 📋\n\n"
        "Your translation management system is running.\n\n"
        "🌐 Web UI: https://tmorder.duckdns.org\n"
        "📅 Calendar: https://tmorder.duckdns.org/calendar/ics?token=rama_tm_secret_2025\n\n"
        "Available commands:\n"
        "/start - Show this message\n"
        "/done - Mark order as delivered\n"
        "/help - Show help\n"
        "/neworder - Create a new order (interactive)\n\n"
        "💡 Use the web interface or /neworder to create and manage orders."
    )

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark order as delivered"""
    # TODO: Extract order ID from context and update via API
    await update.message.reply_text("✅ Order marked as delivered!")


async def undelivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all undelivered orders with deadlines"""
    try:
        response = requests.get(f"{API_URL}/api/orders/undelivered")
        response.raise_for_status()
        orders = response.json()
        if not orders:
            await update.message.reply_text("📋 No undelivered orders.")
            return
        msg = "📋 **Undelivered Orders:**\n\n"
        for order in orders:
            deadline = datetime.fromisoformat(order['deadline_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            msg += f"• ID {order['id']}: {order['customer_name']} - {order['topic']} (Deadline: {deadline})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error fetching undelivered orders: {e}")
        await update.message.reply_text("❌ Error fetching undelivered orders.")


async def undelivered_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List undelivered orders for a specific client"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /undelivered_client <client_name>")
        return
    client_name = ' '.join(context.args)
    try:
        response = requests.get(f"{API_URL}/api/orders/undelivered/{client_name}")
        response.raise_for_status()
        orders = response.json()
        if not orders:
            await update.message.reply_text(f"📋 No undelivered orders for client '{client_name}'.")
            return
        msg = f"📋 **Undelivered Orders for {client_name}:**\n\n"
        for order in orders:
            deadline = datetime.fromisoformat(order['deadline_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            msg += f"• ID {order['id']}: {order['topic']} (Deadline: {deadline})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error fetching undelivered orders for client {client_name}: {e}")
        await update.message.reply_text(f"❌ Error fetching undelivered orders for client '{client_name}'.")


async def delivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all delivered orders with delivery timestamps"""
    try:
        response = requests.get(f"{API_URL}/api/orders/delivered")
        response.raise_for_status()
        orders = response.json()
        if not orders:
            await update.message.reply_text("📋 No delivered orders.")
            return
        msg = "📋 **Delivered Orders:**\n\n"
        for order in orders:
            delivery_time = datetime.fromisoformat(order['updated_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            deadline = datetime.fromisoformat(order['deadline_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            msg += f"• ID {order['id']}: {order['customer_name']} - {order['topic']} (Delivered: {delivery_time}, Deadline: {deadline})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error fetching delivered orders: {e}")
        await update.message.reply_text("❌ Error fetching delivered orders.")


async def delivered_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List delivered orders for a specific client"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /delivered_client <client_name>")
        return
    client_name = ' '.join(context.args)
    try:
        response = requests.get(f"{API_URL}/api/orders/delivered/{client_name}")
        response.raise_for_status()
        orders = response.json()
        if not orders:
            await update.message.reply_text(f"📋 No delivered orders for client '{client_name}'.")
            return
        msg = f"📋 **Delivered Orders for {client_name}:**\n\n"
        for order in orders:
            delivery_time = datetime.fromisoformat(order['updated_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            deadline = datetime.fromisoformat(order['deadline_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            msg += f"• ID {order['id']}: {order['topic']} (Delivered: {delivery_time}, Deadline: {deadline})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error fetching delivered orders for client {client_name}: {e}")
        await update.message.reply_text(f"❌ Error fetching delivered orders for client '{client_name}'.")

# Diagnostic handler for all updates
async def log_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logging.info("Received update")
        if update.message:
            logging.info(f"Message text: {update.message.text}")
    except Exception as e:
        logging.error(f"Error in diagnostic handler: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    logging.info("/help command received")
    await update.message.reply_text(
        "📋 **TM-Order Help**\n\n"
        "This bot provides deadline reminders for your translation orders.\n\n"
        "**Available Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/done - Mark order as delivered\n"
        "/undelivered - List all undelivered orders\n"
        "/undelivered_client <name> - List undelivered orders for specific client\n"
        "/delivered - List all delivered orders\n"
        "/delivered_client <name> - List delivered orders for specific client\n"
        "/neworder - Create a new order (interactive)\n\n"
        "**How to use:**\n"
        "1. Create orders via web UI or /neworder\n"
        "2. Bot will send reminder 24h before deadline\n"
        "3. Use /done to mark as completed\n\n"
        "📅 Subscribe to calendar feed:\n"
        "https://localhost/calendar/ics?token=rama_tm_secret_2025"
    )

async def neworder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("/neworder command received")
    if context.user_data is None:
        context.user_data = {}
    context.user_data['state'] = 'customer'
    await update.message.reply_text("Let's create a new order!\nWho is the customer?")

async def neworder_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_customer: {update.message.text}")
    if context.user_data is None:
        context.user_data = {}
    context.user_data['customer_name'] = update.message.text.strip()
    context.user_data['state'] = 'topic'
    await update.message.reply_text("What is the topic or description?")

async def neworder_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_topic: {update.message.text}")
    if context.user_data is None:
        context.user_data = {}
    context.user_data['topic'] = update.message.text.strip()
    context.user_data['state'] = 'deadline'
    await update.message.reply_text("What is the deadline? (YYYY-MM-DD HH:MM)")

async def neworder_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_deadline: {update.message.text}")
    try:
        deadline = datetime.strptime(update.message.text.strip(), "%Y-%m-%d %H:%M")
        if context.user_data is None:
            context.user_data = {}
        context.user_data['deadline_at'] = deadline.isoformat()
        context.user_data['state'] = 'src_lang'
    except Exception:
        await update.message.reply_text("Invalid format. Please use YYYY-MM-DD HH:MM")
        return
    await update.message.reply_text("Source language? (e.g. en)")

async def neworder_src_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_src_lang: {update.message.text}")
    if context.user_data is None:
        context.user_data = {}
    context.user_data['source_lang'] = update.message.text.strip()
    context.user_data['state'] = 'tgt_lang'
    await update.message.reply_text("Target language? (e.g. hi)")

async def neworder_tgt_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_tgt_lang: {update.message.text}")
    if context.user_data is None:
        context.user_data = {}
    context.user_data['target_lang'] = update.message.text.strip()
    context.user_data['state'] = 'words'
    await update.message.reply_text("Word count? (or type 0 if unknown)")

async def neworder_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"neworder_words: {update.message.text}")
    try:
        wc = int(update.message.text.strip())
    except Exception:
        await update.message.reply_text("Please enter a number for word count.")
        return
    if context.user_data is None:
        context.user_data = {}
    context.user_data['word_count'] = wc
    # Compose order data
    order = {
        "customer_name": context.user_data['customer_name'],
        "topic": context.user_data['topic'],
        "deadline_at": context.user_data['deadline_at'],
        "source_lang": context.user_data['source_lang'],
        "target_lang": context.user_data['target_lang'],
        "word_count": context.user_data['word_count'],
        "telegram_user_id": update.effective_user.id
    }
    # Send to API
    try:
        resp = requests.post(f"{API_URL}/api/orders", json=order)
        if resp.status_code == 200:
            oid = resp.json().get('id')
            await update.message.reply_text(f"✅ Order created! ID: {oid}\nYou will get reminders before the deadline.")
        else:
            await update.message.reply_text(f"Error creating order: {resp.text}")
    except Exception as e:
        await update.message.reply_text(f"API error: {e}")
    if 'state' in context.user_data:
        del context.user_data['state']

async def neworder_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data is None:
        context.user_data = {}
    if 'state' in context.user_data:
        del context.user_data['state']
    await update.message.reply_text("Order creation cancelled.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data is None:
        context.user_data = {}
    state = context.user_data.get('state')
    if state == 'customer':
        await neworder_customer(update, context)
    elif state == 'topic':
        await neworder_topic(update, context)
    elif state == 'deadline':
        await neworder_deadline(update, context)
    elif state == 'src_lang':
        await neworder_src_lang(update, context)
    elif state == 'tgt_lang':
        await neworder_tgt_lang(update, context)
    elif state == 'words':
        await neworder_words(update, context)

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
    application.add_handler(MessageHandler(filters.ALL, log_all_updates))
    application.add_handler(CommandHandler("start", start), group=1)
    application.add_handler(CommandHandler("help", help_command), group=1)
    application.add_handler(CommandHandler("done", done), group=1)
    application.add_handler(CommandHandler("undelivered", undelivered), group=1)
    application.add_handler(CommandHandler("undelivered_client", undelivered_client), group=1)
    application.add_handler(CommandHandler("delivered", delivered), group=1)
    application.add_handler(CommandHandler("delivered_client", delivered_client), group=1)
    application.add_handler(CommandHandler("neworder", neworder_start), group=1)
    application.add_handler(CommandHandler("cancel", neworder_cancel), group=1)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=1)
    # Fallback for unknown commands (after ConversationHandler)
    async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.info(f"Unknown command: {update.message.text}")
        await update.message.reply_text("Unknown command. If you expected /neworder, please check bot logs for diagnostics.")
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command), group=1)
    # Catch-all text handler for diagnostics
    async def catchall_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logging.info(f"Catchall text: {update.message.text}")
    application.add_handler(MessageHandler(filters.TEXT, catchall_text), group=1)
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Bot started")
    
    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
