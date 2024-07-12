from requests.auth import HTTPBasicAuth
import requests

PFSENSE_HOST = 'http://192.168.1.1'
API_KEY = 'de6b87c7d2afb198244c69fbdbe7fbbe'

def get_token():
    url = f'{PFSENSE_HOST}/api/v2/auth/jwt'
    response = requests.post(url, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()['data']['token']

def apply_changes():
    url = f'{PFSENSE_HOST}/api/v2/firewall/apply'
    response = requests.post(url, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()

def add_port_forward_rule(protocol, destination_port, ip_add, local_port, descr):
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward'
    headers = {
        'Content-Type': 'application/json',
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
    response = requests.post(url, headers=headers, json=data, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()

def edit_port_forward_rule(rule_id, ip_add):
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward'
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'id': rule_id,
        'target': ip_add,
    }
    response = requests.patch(url, headers=headers, json=data, auth=HTTPBasicAuth("admin", "pfsense"))

    return response.json()

def delete_port_forward_rule(rule_id):
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forward?id={rule_id}&apply=true'
    response = requests.delete(url, auth=HTTPBasicAuth("admin", "pfsense"))

    return response.json()

def add_firewall_rule(protocol, destination_port, ip_add, descr):
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule'
    headers = {
        'Content-Type': 'application/json',
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
        'tcp_flags_out_of': ['fin'],
    }
    response = requests.post(url, headers=headers, json=data, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()

def edit_firewall_rule(rule_id, ip_add):
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule'
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        'id': rule_id,
        'destination': ip_add,
    }
    response = requests.patch(url, headers=headers, json=data, auth=HTTPBasicAuth("admin", "pfsense"))
    
    return response.json()

def delete_firewall_rule(rule_id):
    url = f'{PFSENSE_HOST}/api/v2/firewall/rule?id={rule_id}'
    response = requests.delete(url, auth=HTTPBasicAuth("admin", "pfsense"))

    return response.json()
    
def get_port_forward_rules():
    url = f'{PFSENSE_HOST}/api/v2/firewall/nat/port_forwards?limit=0&offset=0'
    response = requests.get(url, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()['data']
    
def get_firewall_rules():
    url = f'{PFSENSE_HOST}/api/v2/firewall/rules?limit=0&offset=0'
    response = requests.get(url, auth=HTTPBasicAuth("admin", "pfsense"))
    return response.json()['data']

# https://github.com/jaredhendrickson13/pfsense-api/blob/dbd61d89b93bb85eb64a4ed7b9f477729d8ea9cf/pfSense-pkg-RESTAPI/files/usr/local/pkg/RESTAPI/Models/PortForward.inc
# https://github.com/jaredhendrickson13/pfsense-api/blob/dbd61d89b93bb85eb64a4ed7b9f477729d8ea9cf/pfSense-pkg-RESTAPI/files/usr/local/pkg/RESTAPI/Models/FirewallRule.inc