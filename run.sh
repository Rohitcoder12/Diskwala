#!/bin/bash

# This script will run both the web server and the bot.

# 1. Start the Gunicorn web server for the API in the background.
# The '&' at the end tells it to run in the background.
echo "Starting Gunicorn web server..."
gunicorn api_server:app &

# 2. Start the Telegram bot script in the foreground.
# The script will stay on this line, keeping the service alive.
echo "Starting Telegram bot..."
python telegram_bot.py