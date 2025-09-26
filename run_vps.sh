#!/bin/bash

# --- PUT YOUR SECRETS HERE ---
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_FROM_BOTFATHER"
export API_ENDPOINT="http://127.0.0.1:8000/api/terabox" # Use a common port like 8000

# Start the API server in the background
gunicorn --bind 0.0.0.0:8000 api_server:app &

# Start the bot in the foreground
python3 telegram_bot.py