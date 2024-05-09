import requests
from django.conf import settings
from django.core.cache import cache

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

# create VM POST
def create_vm(node, vmid, config):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/config"
    config = {
    }
    response = session.post(url, data=config)
    return response.json()

# clone VM POST
def clone_vm(node, vmid, newid):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/clone"
    config = {
        'newid': newid,
        'full': 1,
        # 'target': ''
        # 'storage': 'local-lvm',
    }
    response = session.post(url, data=config)
    return response.json()


# delete VM DELETE
def delete_vm(node, vmid):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}"
    response = session.delete(url)
    return response.json()

# start VM POST
def start_vm(node, vmid):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/start"
    response = session.post(url)
    return response.json()

# shutdown VM POST
def shutdown_vm(node, vmid):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"
    response = session.post(url)
    return response.json()

# shutdown VM PUT
def config_vm(node, vmid, cpu_cores, memory_mb, disk_mb):
    session = get_authenticated_session()
    node = "pve"
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"
    config = {
        'cores': cpu_cores,
        'memory': memory_mb,
        'virtio0': disk_mb # example diskmb = 'local-lvm:vm-100-disk-1,size=32G' # TODO angline check 
    }
    response = session.put(url)
    return response.json()

# get vm ip 
def get_vm_ip(node, vmid):
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
    # headers = {
    #     'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    #     'CSRFPreventionToken': 'YOUR_CSRF_TOKEN'
    # }
    # response = requests.get(url, headers=headers, verify=False)  # Verify should ideally be True in production
    response = requests.get(url, verify=False)
    data = response.json()

    # Parsing the response to extract IP addresses
    if 'result' in data:
        interfaces = data['result']
        for interface in interfaces:
            if 'ip-addresses' in interface:
                for ip in interface['ip-addresses']:
                    if ip['ip-address-type'] == 'ipv4':  # or ipv6 if you prefer
                        return ip['ip-address']
    return "No IP address found"




# Create Template - 1. upload ISO, 2. set existing vm to template




