import requests
import json
import re
from urllib.parse import urlparse

def scrape_terabox_link(url: str) -> dict:
    
    session = requests.Session()
    
    # Let's use a very common and modern User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
    }
    session.headers.update(headers)

    try:
        print("Scraper Step 1: Visiting the initial share link...")
        # Visiting the first page sets up necessary cookies in the session automatically
        initial_response = session.get(url, timeout=15)
        initial_response.raise_for_status()

        parsed_url = urlparse(url)
        surl = parsed_url.path.split('/')[-1]

        domain = parsed_url.netloc
        api_url = f"https://{domain}/share/list"
        
        print(f"Scraper Step 2: Calling API at: {api_url}")
        
        params = {
            'app_id': '250528',
            'shorturl': surl,
            'root': '1'
        }
        
        # --- THIS IS THE KEY IMPROVEMENT ---
        # We set the 'Referer' to the original URL, which mimics a real browser.
        api_headers = {
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest' # Common header for API calls
        }
        # The session will automatically send the cookies it got from Step 1.
        api_response = session.get(api_url, params=params, headers=api_headers, timeout=15)
        api_response.raise_for_status()
        data = api_response.json()

        if data.get('errno') != 0:
            # Let's log the actual error message from Terabox
            error_msg = data.get('errmsg', 'API returned an unknown error.')
            print(f"Scraper Error from Terabox: {error_msg}")
            return {"success": False, "message": f"API returned an error: {error_msg}"}

        if data.get('isdir', 0) == 1:
            files = [{"filename": item.get('server_filename'), "size": item.get('size', 0)} for item in data['list']]
            return {"success": True, "type": "folder", "files": files, "folder_name": data.get('share_info', {}).get('server_filename', 'Unknown Folder')}
        else:
            file_info = data['list'][0]
            dlink = file_info.get('dlink')
            if not dlink:
                return {"success": False, "message": "Could not find dlink in the API response."}
            return {
                "success": True, "type": "file", "filename": file_info.get('server_filename'),
                "size": file_info.get('size', 0), "dlink": dlink
            }

    except Exception as e:
        print(f"Scraper: An unexpected error occurred: {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}