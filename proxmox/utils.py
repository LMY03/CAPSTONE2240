import requests

# Parameters
PROXMOX_HOST = 'https://192.168.254.112:8006'
USERNAME = 'root@pam'
PASSWORD = '123456'

# Authenticate
def get_authenticated_session():
    # CA_CRT = '/path/to/ca_bundle.crt'
    CA_CRT = False # Disable SSL certificate verification
    session = requests.Session()
    session.verify = CA_CRT
    response = session.post(
        f"{PROXMOX_HOST}/api2/json/access/ticket",
        data={'username': USERNAME, 'password': PASSWORD},
        verify=CA_CRT
    )
    data = response.json()
    session.headers.update({
    'CSRFPreventionToken': data['data']['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={data['data']['ticket']}"
    })
    return session

# create VM
def create_vm(node, vmid, config):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/config"
    response = session.post(url, data=config)
    return response.json()

# clone VM
def clone_vm(node, vmid, newid):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/clone"
    data = {
        'newid': newid,
        'full': 1,
        # 'target': ''
        # 'storage': 'local-lvm',
    }
    response = session.post(url, data=data)
    if response.status_code != 200:
        return {'error': 'Failed to clone VM', 'status_code': response.status_code, 'details': response.text}
    return response.json()