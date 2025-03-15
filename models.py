from flask_login import UserMixin
from utils.db import JsonDB

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.oauth_provider = user_data.get('oauth_provider')
        self.oauth_id = user_data.get('oauth_id')

    @staticmethod
    def get_by_oauth_id(oauth_id):
        user_data = JsonDB.get_user_by_oauth(oauth_id)
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        user_data = JsonDB.get_user_by_id(user_id)
        return User(user_data) if user_data else None

    @staticmethod
    def create(username, email, oauth_provider, oauth_id):
        user_data = {
            'username': username,
            'email': email,
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id
        }
        created_user = JsonDB.create_user(user_data)
        return User(created_user)

    def get_downloads(self):
        return JsonDB.get_user_downloads(self.id)

    def add_download(self, spotify_url, track_name="Pending..."):
        return JsonDB.add_download(self.id, {
            'spotify_url': spotify_url,
            'track_name': track_name
        })