import requests
import json
import re
from urllib.parse import urlparse, parse_qs

def scrape_terabox_link(url: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml,xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.terabox.com/'
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        print("Scraper Step 1: Visiting the initial share link...")
        initial_response = session.get(url, timeout=15)
        initial_response.raise_for_status()

        parsed_url = urlparse(url)
        surl = parsed_url.path.split('/')[-1]

        # --- THIS IS THE FIX ---
        # Get the domain (e.g., 'www.1024terabox.com') from the original URL
        domain = parsed_url.netloc
        api_url = f"https://{domain}/share/list"
        print(f"Scraper Step 2: Dynamically calling API at: {api_url} with surl: {surl}")
        # --- END OF FIX ---
        
        params = {
            'app_id': '250528',
            'shorturl': surl,
            'root': '1'
        }

        # Also add cookies from the first request to the headers for the second
        session.headers['Cookie'] = '; '.join([f'{c.name}={c.value}' for c in initial_response.cookies])

        api_response = session.get(api_url, params=params, timeout=15)
        api_response.raise_for_status()
        data = api_response.json()

        if data.get('errno') != 0:
            return {"success": False, "message": data.get('errmsg', 'API returned an error.')}

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

    except requests.exceptions.RequestException as e:
        print(f"Scraper: A network error occurred: {e}")
        return {"success": False, "message": f"A network error occurred: {e}"}
    except Exception as e:
        print(f"Scraper: An unexpected error occurred: {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}