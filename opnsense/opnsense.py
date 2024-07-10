from decouple import config
import json, requests
from requests.auth import HTTPBasicAuth

OPNSENSE_HOST = "http://192.168.12.1"
API_KEY = "5YXDbThp4rmCXf7RS0+Ra1wjPyA/zTkPVesVo6Cpag0IFyhhsEXXy904gW/6tut1uYA1KJbUQ1qKoZTG"
API_SECRET = "ihdQ2hj4TkIcuoZMEcUZv9VYbnt3aL6q6nzJHU+HtSfGbq2fchQBCA9vLZg/uh3uYwSNnKDr1oQ2jgIz"
# CA_CRT = config('CA_CRT')
CA_CRT = False


def add_firewall_rule():
    print('-------------------------')
    url = f"{OPNSENSE_HOST}/api/firewall/nat/forward/addRule"
    headers = {
        'Content-Type': 'application/json'
    }

    data = {"rule" :
        {
        "action": "pass",
  "interface": "wan",
  "description": "rule_description",
  "source_net": "192.168.0.0/24",
  "protocol": "TCP",
  "destination_net": "10.0.0.0/24"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, verify=CA_CRT, auth=(API_KEY, API_SECRET))

        if response.status_code == 200:
            print("Success:", response.json())
            return response.json()
        else:
            print("Error adding rule:", response.status_code)
            print("Response Headers:", response.headers)
            print("Response Content:", response.text)
            return response

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None

def get_firewall_rule(rule_uuid):
    print('-------------------------')
    url = f"{OPNSENSE_HOST}/api/firewall/filter/getRule?uuid={rule_uuid}"

    try:
        response = requests.get(url, verify=CA_CRT, auth=(API_KEY, API_SECRET))

        if response.status_code == 200:
            print("Success:", response.json())
            return response.json()
        else:
            print("Error adding rule:", response.status_code)
            print("Response Headers:", response.headers)
            print("Response Content:", response.text)
            return response

    except requests.exceptions.RequestException as e:
        print("Request failed:", e)
        return None

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