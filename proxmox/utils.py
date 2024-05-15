import requests
from django.conf import settings
from django.core.cache import cache
import time

# Parameters
PROXMOX_HOST = 'https://192.168.43.201:8006'
USERNAME = 'root@pam'
PASSWORD = '43210'

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


def get_vm_status(node, vmid):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/current"
    response = session.get(url)
    return response.json()

# create VM POST
def create_vm(node, vmid, config):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/config"
    config = {
    }
    response = session.post(url, data=config)
    return response.json()

# clone VM POST
def clone_vm(node, vmid, newid):                    # TODO: how to keep track on the available vmid, need new name
                                                    # TODO: need to make sure there are enough disk space in the server before cloning the machine
    session = get_authenticated_session()
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
    # shutdown vm before deleting them
    #   1. check status
    #   2. if status is running -> shutdown (response['data']['qmpstatus'] = running) 
    #   3. wait for it to shut down
    shutdown_vm(node, vmid)
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}"
    response = session.delete(url)
    return response.json()

# start VM POST
def start_vm(node, vmid):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/start"
    response = session.post(url)
    return response.json()

# # shutdown VM POST
# def shutdown_vm(node, vmid):
#     session = get_authenticated_session()
#     status_url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/current"
#     status_response = session.get(status_url)
#     if status_response.json().get('data', {}).get('status') == 'running':
#         url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"
#         response = session.post(url)
#         # Wait and check status
#         time.sleep(30)  # wait 30 seconds before checking
#         status_response = session.get(status_url)
#         if status_response.json().get('data', {}).get('status') != 'stopped':
#             # Consider further actions if still not stopped
#             print("Shutdown may be stuck, consider further actions.")
#         return response.json()
#     else:
#         return {'error': 'VM is not running, cannot shutdown.'}

# shutdown VM POST
def shutdown_vm(node, vmid):              
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"
    response = session.post(url)
    return response.json()

# stop VM POST - only on special occasion like the vm get stuck
def stop_vm(node, vmid):              
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/stop"
    response = session.post(url)
    return response.json()

# config VM PUT, only working for cpu and ram
def config_vm(node, vmid, cpu_cores, memory_mb, disk, disk_mb):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/config"
    config = {
        'cores': cpu_cores,
        'memory': memory_mb,
        # disk : disk_mb # example diskmb = 'local-lvm:vm-100-disk-1,size=32G' # TODO what should be the key 
    }
    response = session.put(url, data=config)
    return response.json()

def resize_vm(node, vmid, disk, disk_mb):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/resize"
    disk_config={
        'disk' : disk,
        'size' : disk_mb
    }
    response = session.put(url, data=disk_config)
    return response.json()


# run command to change the size of the storage, i guess need qemu agent too
def execute_script(node, vmid, script_path):
    session = get_authenticated_session()  # Make sure you have a function to handle authentication
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/agent/exec"
    command = f"bash {script_path}"
    data = {
        'command': command
    }
    response = session.post(url, data=data)
    return response.json()



# get vm ip # TODO: need guest agent installed before getting ip address
def get_vm_ip(node, vmid):
    session = get_authenticated_session()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
    # headers = {
    #     'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    #     'CSRFPreventionToken': 'YOUR_CSRF_TOKEN'
    # }
    # response = requests.get(url, headers=headers, verify=False)  # Verify should ideally be True in production
    response = session.get(url, verify=False)
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
def create_vm_template(node, iso_path, storage_name):
    session = get_authenticated_session()
    # 1. upload ISO
    upload_ISO(session, node, iso_path, storage_name)

    # 2. create vm using this iso, how to remove the hardware?
    
    
    # 2. set existing vm to template
    convert_template()
    
    

def upload_ISO(session, node, iso_path, storage_name):
    upload_url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/storage/{storage_name}/upload"
    files = {
        'filename': ('filename', open(iso_path, 'rb'), 'application/octet-stream'),
        'content': (None, 'iso')
    }

    response = session.get(upload_url, files=files, verify=False)
    return response.json()

def convert_template():
    return