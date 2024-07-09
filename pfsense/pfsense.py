import json, requests

PFSENSE_HOST = '192.168.1.1'
API_KEY = '3cbd65d72ccb0bba75e669d2679f54f5'

def add_firewall_rule():
    # url = f"{PFSENSE_HOST}/api/v2/firewall/apply"
    url = f"{PFSENSE_HOST}/api/v2/firewall/rule"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': API_KEY
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

    response = requests.post(url, headers=headers, json=data)

    return response.json()