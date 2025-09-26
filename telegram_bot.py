import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Configuration ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # <-- PASTE YOUR BOT TOKEN HERE
YOUR_API_ENDPOINT = "http://127.0.0.1:5000/api/terabox"

# Function to format file size in a readable way
def format_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the user sends /start."""
    await update.message.reply_text('Hello! Send me any Terabox link (file or folder) and I will process it for you.')

async def handle_terabox_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles messages containing Terabox links."""
    message_text = update.message.text
    
    # Check if the message contains a valid Terabox link
    if 'terabox.com' in message_text or 'terabox.app' in message_text:
        processing_message = await update.message.reply_text("⏳ Found a Terabox link! Processing, please wait...")
        
        try:
            # Call your custom API with the link
            api_response = requests.get(YOUR_API_ENDPOINT, params={'url': message_text}, timeout=60)
            api_response.raise_for_status()
            
            data = api_response.json()
            
            if data.get('success'):
                # Check if it's a file or a folder
                if data['type'] == 'file':
                    filename = data.get('filename', 'Unknown File')
                    size = format_size(data.get('size', 0))
                    dlink = data.get('dlink')
                    reply_message = (
                        f"✅ **File Found!**\n\n"
                        f"**Name:** `{filename}`\n"
                        f"**Size:** `{size}`\n\n"
                        f"**Direct Link:**\n`{dlink}`"
                    )
                elif data['type'] == 'folder':
                    folder_name = data.get('folder_name', 'Unknown Folder')
                    files = data.get('files', [])
                    
                    if not files:
                        reply_message = f"📁 **Folder Found: {folder_name}**\n\nThis folder appears to be empty."
                    else:
                        file_list_text = ""
                        for file in files[:20]: # Show up to 20 files to avoid message limit
                            filename = file.get('filename', 'Unknown File')
                            size = format_size(file.get('size', 0))
                            file_list_text += f"- `{filename}` ({size})\n"
                        
                        reply_message = (
                            f"📁 **Folder Found: {folder_name}**\n\n"
                            f"Here are the files inside:\n{file_list_text}\n"
                            f"*Note: Folder downloads are not yet supported. You can send a link to an individual file.*"
                        )
            else:
                error_message = data.get('message', 'An unknown error occurred.')
                reply_message = f"❌ **Error:** {error_message}"

        except requests.exceptions.RequestException as e:
            reply_message = f"❌ Error: Could not connect to the processing API. Please ensure it is running. Details: {e}"
        
        await processing_message.edit_text(reply_message, parse_mode='Markdown')

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_terabox_link))
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()