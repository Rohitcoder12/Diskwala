import requests
import json
import re

def scrape_terabox_link(url: str) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        match = re.search(r'var yukon_data = (\{.*?\});', response.text)
        if not match: return {"success": False, "message": "Could not find page data."}
        data = json.loads(match.group(1))
        if not data.get('list'): return {"success": False, "message": data.get('error_msg', 'Link is invalid or expired.')}

        if data.get('isdir', 0) == 1:
            files = [{"filename": item.get('server_filename'), "size": item.get('size', 0)} for item in data['list']]
            return {"success": True, "type": "folder", "files": files, "folder_name": data.get('title', 'Unknown Folder')}
        else:
            file_info = data['list'][0]
            fs_id = file_info.get('fs_id')
            if not fs_id: return {"success": False, "message": "Could not find file ID."}
            api_url = "https://www.terabox.com/api/filemetas"
            params = {'app_id': '250528', 'fsid': str(fs_id), 'dlink': '1', 'web': '1'}
            api_response = session.get(api_url, params=params)
            api_data = api_response.json()
            if api_data.get('errno') == 0 and 'dlink' in api_data:
                return {"success": True, "type": "file", "filename": file_info.get('server_filename'), "size": file_info.get('size', 0), "dlink": api_data['dlink']}
            else: return {"success": False, "message": "Failed to get direct link from API."}
    except Exception as e: return {"success": False, "message": f"An error occurred: {e}"}