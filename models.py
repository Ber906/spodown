from flask_login import UserMixin
from utils.db import JsonDB
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')

    @staticmethod
    def get_by_email(email):
        user_data = JsonDB.get_user_by_email(email)
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_id(user_id):
        user_data = JsonDB.get_user_by_id(user_id)
        return User(user_data) if user_data else None

    @staticmethod
    def create(username, email, password):
        user_data = {
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password)
        }
        created_user = JsonDB.create_user(user_data)
        return User(created_user)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_downloads(self):
        return JsonDB.get_user_downloads(self.id)

    def add_download(self, spotify_url, track_name="Pending..."):
        return JsonDB.add_download(self.id, {
            'spotify_url': spotify_url,
            'track_name': track_name
        })