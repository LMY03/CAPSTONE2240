import requests
import json

# GUACAMOLE_HOST = 'http://guacamole:8080'
GUACAMOLE_HOST = "http://10.1.200.20:8080"
# GUACAMOLE_HOST = 'http://192.168.254.125:8080'
USERNAME = 'guacadmin'
PASSWORD = 'guacadmin'

# get token /
def get_token():
    # CA_CRT = '/path/to/ca_bundle.crt'
    # CA_CRT = False # Disable SSL certificate verification
    session = requests.Session()
    # session.verify = CA_CRT
    response = session.post(
        f"{GUACAMOLE_HOST}/guacamole/api/tokens",
        data={'username': USERNAME, 'password': PASSWORD},
        # verify=CA_CRT
    )
    data = response.json()
    return data['authToken']

# get session info TODO: avoid request again here
def get_session_info():
    session = requests.Session()
    response = session.post(
        f"{GUACAMOLE_HOST}/guacamole/api/tokens",
        data={'username': USERNAME, 'password': PASSWORD},
    )
    data = response.json()    
    session.headers.update({
      'Guacamole-Token': data['authToken'],
    })
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections"
    response = session.get(url)

    return response.text

# create user 200
def create_user(username, password):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/users?token={token}"
    config = {
        "username": username,
        "password": password,
        "attributes": {
            "disabled": "",
            "expired": "",
            "access-window-start": "",
            "access-window-end": "",
            "valid-from": "",
            "valid-until": "",
            "timezone": ""
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(config), headers=headers)
    return response.status_code

# delete user 204
def delete_user(username):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/users/{username}?token={token}"
    response = requests.delete(url)
    return response

# create connection 200
def create_connection(name, protocol, port, hostname, username, password, parent_identifier):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections?token={token}"
    config = {
      "parentIdentifier": parent_identifier,
      "name": name,
      "protocol": protocol,
      "parameters": {
        "port": port,
        "hostname": hostname,
        "username": username,
        "password": password
      },
      "attributes": {}
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(config), headers=headers)

    # get connection id
    data = response.json()
    return data["identifier"]

# delete connection 204
def delete_connection(connection_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections/{connection_id}?token={token}"
    response = requests.delete(url)
    return response

def get_connection_details(connection_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections/{connection_id}?token={token}"
    # headers = {'Authorization': f'Bearer {token}'}
    # response = requests.get(url, headers=headers)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_connection_parameter_details(connection_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections/{connection_id}/parameters?token={token}"
    # headers = {'Authorization': f'Bearer {token}'}
    # response = requests.get(url, headers=headers)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# update connection 204
def update_connection(connection_id, hostname):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/connections/{connection_id}?token={token}"
    headers = {'Content-Type': 'application/json'}
    connection_details = get_connection_details(connection_id)
    connection_parameter_details = get_connection_parameter_details(connection_id)
    connection_parameter_details['hostname'] = hostname
    connection_details['parameters'] = connection_parameter_details
    updated_data=json.dumps(connection_details)
    response = requests.put(url, data=updated_data, headers=headers)
    return response

# assign connection 204
def assign_connection(username, connection_id):
    return set_permission(username, config=[{
        "op": "add",
        "path": f"/connectionPermissions/{connection_id}",
        "value": "READ"
    }])

# revoke connection 204
def revoke_connection(username, connection_id):
    return set_permission(username, config=[{
        "op": "remove",
        "path": f"/connectionPermissions/{connection_id}",
        "value": "READ"
    }])

# set permission
def set_permission(username, config):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/mysql/users/{username}/permissions?token={token}"
    headers = {'Content-Type': 'application/json'}
    response = requests.patch(url, data=json.dumps(config), headers=headers)
    return response.status_code

def get_connection_url(connection_id, username, password):
    token = get_connection_token(username, password)
    # token = get_token()
    return f"{GUACAMOLE_HOST}/guacamole/#/client/{connection_id}?token={token}"

# def get_connection_token(username, password):
#     url = f"{GUACAMOLE_HOST}/guacamole/api/tokens"
#     config = { 'username': username, 'password': password }
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
#     response = requests.post(url, data=json.dumps(config), headers=headers)
#     data = response.json()
#     return data['authToken']

def get_connection_token(username, password):
    session = requests.Session()
    response = session.post(
        f"{GUACAMOLE_HOST}/guacamole/api/tokens",
        data={'username': username, 'password': password},
    )
    data = response.json()
    return data['authToken']