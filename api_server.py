from flask import Flask, request, jsonify
from terabox_scraper import scrape_terabox_link
import os

app = Flask(__name__)

@app.route('/api/terabox', methods=['GET'])
def handle_terabox_request():
    terabox_url = request.args.get('url')
    if not terabox_url:
        return jsonify({"success": False, "message": "Missing 'url' parameter."}), 400
    result = scrape_terabox_link(terabox_url)
    return jsonify(result)