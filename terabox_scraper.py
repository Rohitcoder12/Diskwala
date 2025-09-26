import requests
import json
import re
from urllib.parse import urlparse, parse_qs

def scrape_terabox_link(url: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.terabox.com/' # Add a referer header
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        print("Scraper Step 1: Visiting the initial share link to get cookies...")
        # We need to visit the page first to get essential cookies
        initial_response = session.get(url, timeout=10)
        initial_response.raise_for_status()

        # Extract the shorturl from the original URL
        parsed_url = urlparse(url)
        surl = parsed_url.path.split('/')[-1]

        print(f"Scraper Step 2: Calling the new /share/list API with surl: {surl}")
        
        # This is the new API endpoint you discovered
        api_url = "https://www.1024terabox.com/share/list"
        
        params = {
            'app_id': '250528',
            'shorturl': surl,
            'root': '1'
        }

        api_response = session.get(api_url, params=params)
        api_response.raise_for_status()
        data = api_response.json()

        # Check for API errors
        if data.get('errno') != 0:
            return {"success": False, "message": data.get('errmsg', 'API returned an error.')}

        # Check if it's a folder or a single file
        if data.get('isdir', 0) == 1:
            print("Scraper: Detected a folder.")
            files = [{"filename": item.get('server_filename'), "size": item.get('size', 0)} for item in data['list']]
            return {"success": True, "type": "folder", "files": files, "folder_name": data.get('share_info', {}).get('server_filename', 'Unknown Folder')}
        else:
            # It's a single file
            print("Scraper: Detected a single file.")
            file_info = data['list'][0]
            
            # The direct link is often included directly in this response now!
            dlink = file_info.get('dlink')
            if not dlink:
                return {"success": False, "message": "Could not find dlink in the API response."}
            
            return {
                "success": True,
                "type": "file",
                "filename": file_info.get('server_filename'),
                "size": file_info.get('size', 0),
                "dlink": dlink
            }

    except requests.exceptions.Timeout:
        return {"success": False, "message": "The request to Terabox timed out."}
    except Exception as e:
        print(f"Scraper: An unexpected error occurred: {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}