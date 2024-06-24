import requests
import json

from .token import get_token

GUACAMOLE_HOST = 'http://guacamole:8080/guacamole'
DATA_SOURCE = 'mysql'

def getHeader(): 
    token = get_token()
    headers = { 'Authorization': f'Bearer {token}' }
    return headers

def create_guacamole_user(username, password):
    data = {
        'username': username,
        'password': password,
        'attributes': {}
    }
    response = requests.post(
        f"{GUACAMOLE_HOST}/api/session/data/{DATA_SOURCE}/users",
        headers=getHeader(),
        json=data
    )
    response.raise_for_status()
    return response.json()

def create_guacamole_connection(name, protocol, parameters):
    data = {
        'name': name,
        'protocol': protocol,
        'parameters': parameters
    }
    response = requests.post(
        f"{GUACAMOLE_HOST}/api/session/data/{DATA_SOURCE}/connections",
        headers=getHeader(),
        json=data
    )
    response.raise_for_status()
    return response.json()