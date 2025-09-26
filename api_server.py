from flask import Flask, request, jsonify
from terabox_scraper import scrape_terabox_link
import os

app = Flask(__name__)

# --- SECURELY GET THE COOKIE ---
# This reads the cookie from the "Environment Variables" you will set on Render.
MY_TERABOX_COOKIE = os.environ.get('TERABOX_COOKIE')

# A check to make sure the cookie is set on the server
if not MY_TERABOX_COOKIE:
    raise ValueError("FATAL ERROR: TERABOX_COOKIE environment variable not set!")

@app.route('/api/terabox', methods=['GET'])
def handle_terabox_request():
    terabox_url = request.args.get('url')
    if not terabox_url:
        return jsonify({"success": False, "message": "Missing 'url' parameter."}), 400
    
    # We now pass the cookie to the scraper function
    result = scrape_terabox_link(terabox_url, MY_TERABOX_COOKIE)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500

# Note: We no longer have the app.run() block. Gunicorn will handle this.