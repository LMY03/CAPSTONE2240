from requests.auth import HTTPBasicAuth
import requests

PFSENSE_HOST = 'http://192.168.1.1'
API_KEY = '74c46c1735cc476bb78df2c189be73daf9753ba872d64f8'

def get_token():
    url = f'{PFSENSE_HOST}/api/v2/auth/jwt'
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(url, headers=headers, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()['data']['token']

def apply_changes():
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/apply'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}",
    }
    response = requests.post(url, headers=headers)
    return response.json()['data']['token']

def add_port_forward_rule(protocol, destination_port, ip_add, local_port, descr):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}",
    }
    data = {
        'interface': 'wan',
        'protocol': protocol,
        'source': 'any',
        # 'source_port': 'any',
        'destination': 'wan:ip',
        'destination_port': destination_port,
        'target': ip_add,
        'local_port': local_port,
        'disabled': False,
        # 'nordr': True, # notsure
        # 'nosync': True,
        'descr': descr,
        'associated_rule_id': '',
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def edit_port_forward_rule(rule_id, ip_add):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}",
    }
    data = {
        'id': rule_id,
        'target': ip_add,
    }
    response = requests.patch(url, headers=headers, json=data)

    return response.json()

def delete_port_forward_rule(rule_id):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward?id={rule_id}&apply=true'
    headers = { 'Authorization': f"Bearer {token}" }
    response = requests.delete(url, headers=headers)

    return response.json()

def add_firewall_rule(protocol, destination_port, ip_add, descr):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}",
    }
    data = {
        'type': 'pass',
        'interface': ['wan'],
        'ipprotocol': 'inet',
        'protocol': protocol,
        'source': 'any',
        'destination': ip_add,
        'destination_port': destination_port,
        'descr': descr,
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def edit_firewall_rule(rule_id, ip_add):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {token}",
    }
    data = {
        'id': rule_id,
        'target': ip_add,
    }
    response = requests.patch(url, headers=headers, json=data)
    
    return response.json()

def delete_firewall_rule(rule_id):
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule?id={rule_id}'
    headers = { 'Authorization': f"Bearer {token}" }
    response = requests.delete(url, headers=headers)

    return response.json()
    
def get_port_forward_rules():
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forwards?limit=0&offset=0'
    headers = { 'Authorization': f"Bearer {token}" }
    response = requests.get(url, headers=headers)
    return response.json()['data']
    
def get_firewall_rules():
    token = get_token()
    url = f'{PFSENSE_HOST}/api/v2/firewall/rules?limit=0&offset=0'
    headers = { 'Authorization': f"Bearer {token}" }
    response = requests.get(url, headers=headers)
    return response.json()['data']

# https://github.com/jaredhendrickson13/pfsense-api/blob/dbd61d89b93bb85eb64a4ed7b9f477729d8ea9cf/pfSense-pkg-RESTAPI/files/usr/local/pkg/RESTAPI/Models/PortForward.inc
# https://github.com/jaredhendrickson13/pfsense-api/blob/dbd61d89b93bb85eb64a4ed7b9f477729d8ea9cf/pfSense-pkg-RESTAPI/files/usr/local/pkg/RESTAPI/Models/FirewallRule.inc