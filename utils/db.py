import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Ensure data directory exists
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# File paths
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DOWNLOADS_FILE = os.path.join(DATA_DIR, "downloads.json")

def load_json(file_path: str) -> dict:
    """Load JSON file, create if not exists"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_json(file_path: str, data: dict):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

class JsonDB:
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        users = load_json(USERS_FILE)
        return next((user for user in users.values() if user.get('email') == email), None)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        users = load_json(USERS_FILE)
        return users.get(user_id)

    @staticmethod
    def create_user(user_data: Dict) -> Dict:
        users = load_json(USERS_FILE)
        user_id = str(len(users) + 1)
        user_data['id'] = user_id
        users[user_id] = user_data
        save_json(USERS_FILE, users)
        return user_data

    @staticmethod
    def add_download(user_id: str, download_data: Dict) -> Dict:
        downloads = load_json(DOWNLOADS_FILE)
        download_id = str(len(downloads) + 1)
        download_data.update({
            'id': download_id,
            'user_id': user_id,
            'download_date': datetime.now().isoformat()
        })
        downloads[download_id] = download_data
        save_json(DOWNLOADS_FILE, downloads)
        return download_data

    @staticmethod
    def get_user_downloads(user_id: str) -> List[Dict]:
        downloads = load_json(DOWNLOADS_FILE)
        return [
            download for download in downloads.values()
            if download['user_id'] == user_id
        ]

    @staticmethod
    def update_download(download_id: str, update_data: Dict) -> Optional[Dict]:
        downloads = load_json(DOWNLOADS_FILE)
        if download_id in downloads:
            downloads[download_id].update(update_data)
            save_json(DOWNLOADS_FILE, downloads)
            return downloads[download_id]
        return None