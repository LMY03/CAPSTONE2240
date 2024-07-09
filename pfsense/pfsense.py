import json, requests

PFSENSE_HOST = 'http://192.168.1.1'
API_KEY = '3cbd65d72ccb0bba75e669d2679f54f5'

def add_firewall_rule():
    # url = f"{PFSENSE_HOST}/api/v2/firewall/apply"
    url = f"{PFSENSE_HOST}/api/v2/firewall/rule"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {API_KEY}"
    }

    data = {
        "interface": "wan",
        "protocol": "tcp/udp",
        "src": "any",
        "srcport": "",
        "dst": "wan_address",
        "dstport": "8000",
        "target": "192.168.1.2",
        "local-port": "8000",
        "descr": "Test",
        "natreflection": "enable",
        "noxmlrpc": 'false',
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}
    
def get_rules():
    url = f"{PFSENSE_HOST}/api/v1/firewall/rule"  # Adjust API version/path as necessary
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {API_KEY}"  # Ensure the correct format
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an error for 4XX or 5XX responses
        return response.json()  # Returns the list of firewall rules
    except requests.RequestException as e:
        return {"error": str(e)}