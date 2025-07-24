import os
import logging
import re
import requests
from bs4 import BeautifulSoup
from threading import Thread
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# --- Configuration ---
# We will get the token from Render's Environment Variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("No TELEGRAM_TOKEN found in environment variables!")

# --- Flask App Setup ---
# This is the minimal web server to keep Render happy
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is alive!"

def run_flask_app():
    # Gunicorn will run this app, so we don't need app.run() here
    # This function is just a placeholder for gunicorn to target
    pass

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Core Scraper Function (Unchanged) ---
def get_diskwala_direct_link(url: str) -> dict or None:
    """
    Scrapes the Diskwala page to find the direct download link.
    Returns a dictionary with link, filename, and size, or None on failure.
    """
    match = re.search(r'diskwala\.com/app/([a-f0-9]+)', url)
    if not match:
        return None

    file_id = match.group(1)
    download_page_url = f"https://www.diskwala.com/download/{file_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        page_response = requests.get(download_page_url, headers=headers, timeout=15)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, 'html.parser')
        download_button = soup.find('a', class_='btn-primary')
        if not download_button or 'href' not in download_button.attrs:
            logger.error(f"Could not find download button for {url}")
            return None
        
        direct_link = download_button['href']
        file_name_tag = soup.find('h5', class_='text-center')
        file_name = file_name_tag.get_text(strip=True) if file_name_tag else f"diskwala_{file_id}"
        size_info_tag = soup.find('p', class_='text-center text-primary')
        file_size = size_info_tag.get_text(strip=True) if size_info_tag else "Unknown size"
        
        return {"link": direct_link, "name": file_name, "size": file_size}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping {url}: {e}")
        return None

# --- Telegram Bot Handlers (Unchanged) ---
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_html(
        f"Hi {user.mention_html()}! 🔥\n\nI am your Diskwala Downloader Bot. "
        "Just send me any Diskwala.com link, and I will get the direct download link for you."
    )

def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_html(
        "<b>How to use me:</b>\n"
        "Simply send me a Diskwala URL (e.g., `https://www.diskwala.com/app/...`).\n\n"
        "I will handle the rest and give you a direct download button!"
    )

def handle_diskwala_link(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    match = re.search(r'(https?://www\.diskwala\.com/app/[a-f0-9]+)', url)
    if not match:
        return

    found_url = match.group(0)
    processing_message = update.message.reply_text("⏳ Fetching your download link, please wait...")
    file_info = get_diskwala_direct_link(found_url)

    if file_info:
        caption = (
            f"✅ **Link Generated Successfully!**\n\n"
            f"📄 **File:** `{file_info['name']}`\n"
            f"💾 **Size:** `{file_info['size']}`"
        )
        keyboard = [[InlineKeyboardButton("🚀 Download Now 🚀", url=file_info['link'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=processing_message.message_id,
            text=caption, reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=processing_message.message_id,
            text="❌ **Error:** Could not extract the link. The file might be deleted or the website has changed."
        )

# --- Main Bot Function ---
def run_bot():
    """Initializes and runs the Telegram bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'diskwala\.com/app/'), handle_diskwala_link))
    
    logger.info("Starting Telegram bot polling...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Gunicorn will run the Flask app. This part is mainly for local testing.
    # On Render, Gunicorn starts the 'app' object directly.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
