from decouple import config
import json, requests
import base64

GUACAMOLE_HOST = config('GUACAMOLE_HOST')
USERNAME = config('GUACAMOLE_USERNAME')
PASSWORD = config('GUACAMOLE_PASSWORD')
DATASOURCE = config('GUACAMOLE_DATASOURCE')
# CA_CRT = config('CA_CRT')
CA_CRT = False

# get token /
def get_token():
   return get_connection_token(USERNAME, PASSWORD)

# def get_token():
#     # CA_CRT = '/path/to/ca_bundle.crt'
#     # CA_CRT = False # Disable SSL certificate verification
#     session = requests.Session()
#     # session.verify = CA_CRT
#     response = session.post(
#         f"{GUACAMOLE_HOST}/guacamole/api/tokens",
#         data={'username': USERNAME, 'password': PASSWORD},
#         # verify=CA_CRT
#     )
#     data = response.json()
#     return data['authToken']

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
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections"
    response = session.get(url)

    return response.text

# create user 200
def create_user(username, password):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/users?token={token}"
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
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/users/{username}?token={token}"
    response = requests.delete(url)
    return response

# create connection 200
def create_connection(name, protocol, port, hostname, username, password, parent_identifier):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections?token={token}"
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
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections/{connection_id}?token={token}"
    response = requests.delete(url)
    return response

def get_connection_details(connection_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections/{connection_id}?token={token}"
    # headers = {'Authorization': f'Bearer {token}'}
    # response = requests.get(url, headers=headers)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_connection_parameter_details(connection_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections/{connection_id}/parameters?token={token}"
    # headers = {'Authorization': f'Bearer {token}'}
    # response = requests.get(url, headers=headers)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# update connection 204
def update_connection(connection_id, hostname):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connections/{connection_id}?token={token}"
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
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/users/{username}/permissions?token={token}"
    headers = {'Content-Type': 'application/json'}
    response = requests.patch(url, data=json.dumps(config), headers=headers)
    return response.status_code

def create_connection_group(name):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connectionGroups?token={token}"
    config = {
        "parentIdentifier": "ROOT",
        "name": name,
        "type": "ORGANIZATIONAL",
        "attributes": {
            "max-connections": "",
            "max-connections-per-user": "",
            "enable-session-affinity": ""
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(config), headers=headers)

    # get connection id
    data = response.json()
    return data['identifier']

def delete_connection_group(connection_group_id):
    token = get_token()
    url = f"{GUACAMOLE_HOST}/guacamole/api/session/data/{DATASOURCE}/connectionGroups/{connection_group_id}?token={token}"
    response = requests.delete(url)
    return response

def assign_connection_group(username, connection_group_id):
    return set_permission(username, config=[{
        "op": "add",
        "path": f"/connectionGroupPermissions/{connection_group_id}",
        "value": "READ"
    }])

def revoke_connection_group(username, connection_group_id):
    return set_permission(username, config=[{
        "op": "remove",
        "path": f"/connectionGroupPermissions/{connection_group_id}",
        "value": "READ"
    }])

def get_connection_url(connection_id, username, password):
    token = get_connection_token(username, password)
    original_string = f'{connection_id}\0c\0{DATASOURCE}'
    string_bytes = original_string.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return f"{config('WAN_ADDRESS')}:8080/guacamole/#/client/{base64_string}?token={token}"

# def get_connection_token(username, password):
#     url = f"{GUACAMOLE_HOST}/guacamole/api/tokens"
#     config = { 'username': username, 'password': password }
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
#     response = requests.post(url, data=json.dumps(config), headers=headers)
#     data = response.json()
#     return data['authToken']

def get_connection_token(username, password):
    # CA_CRT = '/path/to/ca_bundle.crt'
    # CA_CRT = False # Disable SSL certificate verification
    session = requests.Session()
    session.verify = CA_CRT
    response = session.post(
        f"{GUACAMOLE_HOST}/guacamole/api/tokens",
        data={'username': username, 'password': password},
    )
    data = response.json()

    return data['authToken']

# https://sourceforge.net/p/guacamole/discussion/1110834/thread/fb609070/#bec4