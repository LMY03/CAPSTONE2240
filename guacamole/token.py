import requests
import time

GUACAMOLE_HOST = 'http://guacamole:8080/guacamole'
USERNAME = 'guacadmin'
PASSWORD = 'guacadmin'

def __init__(self):
    self.token = None
    self.expiry_time = None

def get_token(self):
    if self.token is None or self.is_token_expired():
        self.refresh_token()
    return self.token

def is_token_expired(self):
    return self.expiry_time is None or time.time() >= self.expiry_time

def refresh_token(self):
    response = requests.post(
        f"{GUACAMOLE_HOST}/api/tokens",
        data={
            'username': USERNAME,
            'password': PASSWORD
        }
    )
    response.raise_for_status()
    data = response.json()
    self.token = data.get('authToken')
    self.expiry_time = time.time() + data.get('expires')  # Assuming 'expires' is in seconds

