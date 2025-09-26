from flask import Flask, request, jsonify
from terabox_scraper import scrape_terabox_link

app = Flask(__name__)

@app.route('/api/terabox', methods=['GET'])
def handle_terabox_request():
    # We now expect a 'url' parameter
    terabox_url = request.args.get('url')

    if not terabox_url:
        return jsonify({"success": False, "message": "Missing 'url' parameter."}), 400

    # Call our new scraper function
    result = scrape_terabox_link(terabox_url)

    # Return the result from the scraper directly to the bot
    if result["success"]:
        return jsonify(result)
    else:
        # If the scraper failed, return an error message
        return jsonify(result), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
