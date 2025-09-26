import requests
import json
import re
from urllib.parse import urlparse

def scrape_terabox_link(url: str) -> dict:
    """
    Scrapes a public Terabox link to find either a direct download link (for a file)
    or a list of files (for a folder).

    Returns a dictionary with the results.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    session = requests.Session()
    session.headers.update(headers)

    try:
        print(f"Scraper: Fetching page for URL: {url}")
        response = session.get(url, timeout=10)
        response.raise_for_status()

        # Find the big JSON blob of data in the page's HTML
        match = re.search(r'var yukon_data = (\{.*?\});', response.text)
        if not match:
            print("Scraper: Could not find yukon_data in the page.")
            return {"success": False, "message": "Could not find data on the page."}

        data = json.loads(match.group(1))

        # Check if the link is valid or not expired
        if not data.get('list'):
            error_message = "Link is invalid, expired, or deleted."
            if 'error_msg' in data:
                error_message = data['error_msg']
            return {"success": False, "message": error_message}

        # Check if it's a folder or a single file
        if data.get('isdir', 0) == 1:
            # It's a folder
            print("Scraper: Detected a folder.")
            folder_contents = []
            for item in data['list']:
                folder_contents.append({
                    "filename": item.get('server_filename'),
                    "size": item.get('size', 0)
                })
            return {
                "success": True,
                "type": "folder",
                "files": folder_contents,
                "folder_name": data.get('title', 'Unknown Folder')
            }
        else:
            # It's a single file
            print("Scraper: Detected a single file.")
            file_info = data['list'][0]
            fs_id = file_info.get('fs_id')
            if not fs_id:
                return {"success": False, "message": "Could not find file ID."}

            # Now we call the internal API to get the direct link
            api_url = "https://www.terabox.com/api/filemetas"
            params = {'app_id': '250528', 'fsid': str(fs_id), 'dlink': '1', 'web': '1'}
            
            api_response = session.get(api_url, params=params)
            api_data = api_response.json()

            if api_data.get('errno') == 0 and 'dlink' in api_data:
                return {
                    "success": True,
                    "type": "file",
                    "filename": file_info.get('server_filename'),
                    "size": file_info.get('size', 0),
                    "dlink": api_data['dlink']
                }
            else:
                return {"success": False, "message": "Failed to retrieve direct link from API."}

    except requests.exceptions.Timeout:
        return {"success": False, "message": "The request to Terabox timed out."}
    except Exception as e:
        print(f"Scraper: An unexpected error occurred: {e}")
        return {"success": False, "message": f"An unexpected error occurred: {e}"}
