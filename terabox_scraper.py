import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

# --- SECURELY GET SECRETS FROM RENDER'S ENVIRONMENT ---
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
YOUR_API_ENDPOINT = os.environ.get('API_ENDPOINT')

# Check if the variables were set correctly on Render
if not TELEGRAM_BOT_TOKEN or not YOUR_API_ENDPOINT:
    raise ValueError("FATAL ERROR: A required environment variable (TELEGRAM_BOT_TOKEN or API_ENDPOINT) is not set!")

# Function to format file size in a readable way
def format_size(size_bytes):
    if size_bytes == 0: return "0B"
    import math
    names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {names[i]}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! Send any Terabox link to process.')

async def handle_terabox_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = update.message.text
    if 'terabox.com' in message_text or 'terabox.app' in message_text:
        processing_message = await update.message.reply_text("⏳ Processing...")
        try:
            # The bot calls its own API server running in the same service
            api_response = requests.get(YOUR_API_ENDPOINT, params={'url': message_text}, timeout=60)
            api_response.raise_for_status()
            data = api_response.json()
            if data.get('success'):
                if data['type'] == 'file':
                    reply_message = f"✅ **File:** `{data['filename']}`\n**Size:** `{format_size(data['size'])}`\n\n**Link:**\n`{data['dlink']}`"
                elif data['type'] == 'folder':
                    file_list = "".join([f"- `{f['filename']}` ({format_size(f['size'])})\n" for f in data['files'][:20]])
                    reply_message = f"📁 **Folder:** `{data['folder_name']}`\n\nFiles inside:\n{file_list}\n*Folder downloads not supported.*"
            else: reply_message = f"❌ **Error:** {data.get('message', 'Unknown error.')}"
        except Exception as e: reply_message = f"❌ Error connecting to API: {e}"
        await processing_message.edit_text(reply_message, parse_mode='Markdown')

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_terabox_link))
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()