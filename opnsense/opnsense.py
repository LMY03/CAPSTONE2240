from decouple import config
import json, requests

OPNSENSE_HOST = config('OPNSENSE_HOST')
API_KEY = config('OPNSENSE_API_KEY')
API_SECRET = config('OPNSENSE_API_SECRET')
# CA_CRT = config('CA_CRT')
CA_CRT = False

def add_firewall_rule(ip_add, source_port, destination_port, protocol):
    url = f"{OPNSENSE_HOST}/api/firewall/rule/add"
    payload = {
        "rule": {
            "disabled": "0",
            "type": "pass",
            "interface": "wan",
            "protocol": protocol,
            "source": { "any": "1" },
            "destination": {
                "address": "wanip",
                "port": destination_port
            },
            "target": {
                "address": ip_add,
                "port": source_port
            }
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}:{API_SECRET}'
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload), verify=CA_CRT)
    
    return response.json().get('uuid')

def delete_firewall_rule(rule_uuid):
    url = f"{OPNSENSE_HOST}/api/firewall/rule/del/{rule_uuid}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}:{API_SECRET}'
    }
    
    response = requests.post(url, headers=headers, verify=CA_CRT)

    return response

# Function to update a firewall rule
def update_firewall_rule(rule_uuid, ip_add, source_port, destination_port, protocol, disabled="0"):
    url = f"{OPNSENSE_HOST}/api/firewall/rule/set/{rule_uuid}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}:{API_SECRET}'
    }

    payload = {
        "rule": {
            "disabled": disabled,
            "type": "pass",
            "interface": "wan",
            "protocol": protocol,
            "source": { "any": "1" },
            "destination": {
                "address": "wanip",
                "port": destination_port
            },
            "target": {
                "address": ip_add,
                "port": source_port
            }
        }
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload), verify=CA_CRT)

    return response