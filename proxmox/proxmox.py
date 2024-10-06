from decouple import config
import requests, asyncio, time

from proxmoxer import ProxmoxAPI

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROXMOX_HOST = config('PROXMOX_HOST')
PROXMOX_USERNAME = config('PROXMOX_USERNAME')
PROXMOX_PASSWORD = config('PROXMOX_PASSWORD')
PROXMOX_IP = config('PROXMOX_IP')
PROXMOX_PORT = config('PROXMOX_PORT')
# CA_CRT = config('CA_CRT')
CA_CRT = False

# def get_proxmox_ticket():
#     url = f"{PROXMOX_HOST}/api2/json/access/ticket"
#     data = { 'username': PROXMOX_USERNAME, 'password': PROXMOX_PASSWORD }
#     response = requests.post(url, data=data, verify=CA_CRT)
#     if response.status_code != 200:
#         time.sleep(5)
#         return get_proxmox_ticket()
#     return response.json()['data']['CSRFPreventionToken']

# # Authenticate
# def get_authenticated_session():
#     data = get_proxmox_ticket()
#     session = requests.Session()
#     session.verify = CA_CRT
#     session.headers.update({
#         'CSRFPreventionToken': data['data']['CSRFPreventionToken'],
#         'Authorization': f"PVEAuthCookie={data['data']['ticket']}",
#         # 'Cookie': f"PVEAuthCookie={data['data']['ticket']}",
#     })
#     return session

def get_ticket():
    url = f"{PROXMOX_HOST}/api2/json/access/ticket"
    data = { 'username': PROXMOX_USERNAME, 'password': PROXMOX_PASSWORD }
    
    try:
        response = requests.post(url, data=data, verify=CA_CRT, timeout=10)
        response.raise_for_status()
        return response.json()['data']
    except requests.exceptions.RequestException as e:
        print(f"Error getting ticket: {e}")
        time.sleep(5)
        return get_ticket()

def get_task_status(node, upid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/tasks/{upid}/status"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.get(url, headers=headers, verify=CA_CRT, timeout=10)
    if response.status_code != 200 : return get_task_status(node, upid)
    return response.json()

def get_qemu_status(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/agent/info"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.get(url, headers=headers, verify=CA_CRT)

    return response.status_code

def get_vm_ip(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.get(url, headers=headers, verify=CA_CRT)
    return response.json()

# get VM status
def get_vm_status(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/current"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.get(url, headers=headers, verify=CA_CRT)

    status = response.json()['data']['qmpstatus']

    return status

def get_token_sync():
    return get_ticket()

def clone_vm(node, vmid, newid, name):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/clone"
    config = {
        'newid': newid,
        'full': 1,
        'name': name,
        # 'target': ''
        # 'storage': 'local-lvm',
    }
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.post(url, headers=headers, data=config, verify=CA_CRT)
    if response.status_code != 200 : return clone_vm(node, vmid, newid, name)

    return response.json()['data']

# delete VM DELETE
def delete_vm(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.delete(url, headers=headers, verify=CA_CRT)
    if response.status_code != 200 : return delete_vm(node, vmid)
    return response.json()

# start VM POST
def start_vm(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/start"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.post(url, headers=headers, verify=CA_CRT)
    return response.json()

# shutdown VM POST
def shutdown_vm(node, vmid):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/shutdown"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.post(url, headers=headers, verify=CA_CRT)
    return response.json()

# stop VM POST - only on special occasion like the vm get stuck
def stop_vm(node, vmid):              
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/status/stop"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.post(url, headers=headers, verify=CA_CRT)
    return response.json()

def change_vm_name(node, vm_id, vm_name):
    config_vm(node, vm_id, { 'name' : vm_name, })

def config_vm_core_memory(node, vm_id, cpu_cores, memory_mb):
    config_vm(node, vm_id, {
        'cores': cpu_cores,
        'memory': memory_mb,
    })

# configure VM PUT 
def config_vm(node, vmid, config):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/config"
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.put(url, headers=headers, data=config, verify=CA_CRT)
    if response.status_code != 200 : return config_vm(node, vmid, config)
    return response.json()

def config_vm_disk(node, vmid, size):
    token = get_ticket()
    url = f"{PROXMOX_HOST}/api2/json/nodes/{node}/qemu/{vmid}/resize"
    config = {
        'disk': 'scsi0',
        'size': size,
    }
    headers = {
        'CSRFPreventionToken': token['CSRFPreventionToken'],
        'Cookie': f"PVEAuthCookie={ token['ticket'] }",
    }
    response = requests.put(url, headers=headers, data=config, verify=CA_CRT)
    return response.json()

def wait_for_task(node, upid):
    while True:
        task_status = get_task_status(node, upid)
        if task_status['data']['status'] == 'stopped' : return task_status['data']['exitstatus'] # OK
        time.sleep(5)

def wait_for_vm_start(node, vmid):
    while True:
        status = get_vm_status(node, vmid)
        if status == "running" : return status
        time.sleep(5)

def wait_for_vm_stop(node, vmid):
    while True:
        status = get_vm_status(node, vmid)
        if status == "stopped" : return status
        time.sleep(5)

def wait_and_fetch_vm_ip(node, vmid):
    while True:
        response = get_vm_ip(node, vmid)
        if response['data'] != None :
            for interface in response['data']['result']:
                if interface['name'] == "ens18":
                    if 'ip-addresses' not in interface: continue  
                    for ip in interface['ip-addresses']:
                        if ip['ip-address-type'] == 'ipv4':
                            return ip['ip-address']
        time.sleep(5)

###########################################################################################################

def get_proxmox_client():
    proxmox = ProxmoxAPI(
        host=PROXMOX_IP,
        user=PROXMOX_USERNAME,
        password=PROXMOX_PASSWORD,
        verify_ssl=CA_CRT
    )
    return proxmox

def convert_to_template(node, vm_id):
    print(f"Converting container {vm_id} to a template...")
    get_proxmox_client().nodes(node).lxc(vm_id).template().create()
    print(f"Container {vm_id} has been converted to a template.")

    wait_for_template_conversion(node, vm_id)

def wait_for_template_conversion(node, vm_id, timeout=300, interval=5):
    """Wait until the container is successfully converted to a template."""
    print(f"Waiting for container {vm_id} to complete template conversion...")
    total_time = 0
    while total_time < timeout:
        # Check the current status of the container
        config = get_proxmox_client().nodes(node).lxc(vm_id).status.current().get()
        if config.get('template', 0) == 1:  # 'template' field becomes 1 when it's a template
            print(f"Container {vm_id} is now a template.")
            return True
        print(f"Container {vm_id} is still converting to a template, waiting...")
        time.sleep(interval)
        total_time += interval
    raise TimeoutError(f"Container {vm_id} did not convert to a template after {timeout} seconds.")

def create_snapshot(node, vm_id, snapshot_name="automation_snapshot"):
    get_proxmox_client().nodes(node).lxc(vm_id).snapshot().create(snapname=snapshot_name)
    return snapshot_name

def delete_snapshot(node, vm_id, snapshot_name):
    get_proxmox_client().nodes(node).lxc(vm_id).snapshot(snapshot_name).delete()

def clone_container(node, vm_id, snapshot, new_vm_id, new_vm_name):
    wait_for_unlock(node, vm_id)
    get_proxmox_client().nodes(node).lxc(vm_id).clone().create(
        newid=new_vm_id,
        hostname=new_vm_name,
        full=1,
        snapname=snapshot
    )

def clone_lxc(node, template_id, new_vm_id, new_vm_name):
    print(f"Cloning new container {new_vm_id} ({new_vm_name}) from template {template_id}...")
    get_proxmox_client().nodes(node).lxc(template_id).clone().create(
        newid=new_vm_id,
        hostname=new_vm_name,
        full=1,
    )
    print(f"Clone {new_vm_id} ({new_vm_name}) created successfully.")

def shutdown_lxc(node, vm_id):
    get_proxmox_client().nodes(node).lxc(vm_id).status.shutdown().post()

def stop_lxc(node, vm_id):
    get_proxmox_client().nodes(node).lxc(vm_id).status.stop().post()

def delete_lxc(node, vm_id):
    get_proxmox_client().nodes(node).lxc(vm_id).delete()

# # configure VM PUT 
def config_lxc(node, vm_id, cpu_cores, memory_mb):
    get_proxmox_client().nodes(node).lxc(vm_id).config.put(
        cores=cpu_cores,
        memory=memory_mb,
    )

def change_lxc_name(node, vm_id, cpu_cores, memory_mb):
    get_proxmox_client().nodes(node).lxc(vm_id).config.put(
        cores=cpu_cores,
        memory=memory_mb,
    )

def get_lxc_status(node, vm_id):
    return get_proxmox_client().nodes(node).lxc(vm_id).status.current().get()

def is_template_locked(node, vm_id):
    """
    Check if the template or container is locked.
    :param node: Proxmox node name.
    :param vm_id: ID of the VM or container.
    :return: True if locked, False otherwise.
    """
    # Query the status of the template/container
    status = get_proxmox_client().nodes(node).lxc(vm_id).status.current().get()
    return 'lock' in status

def wait_for_template_unlock(node, vm_id, timeout=300, interval=5):
    """
    Wait until the template is unlocked.
    :param node: Proxmox node name.
    :param vm_id: ID of the template/container.
    :param timeout: Maximum time to wait (in seconds).
    :param interval: Time interval between checks (in seconds).
    :return: True if unlocked within timeout, False otherwise.
    """
    total_time = 0
    while total_time < timeout:
        # Check if the template is locked
        if not is_template_locked(node, vm_id):
            print(f"Template {vm_id} is now unlocked and ready for cloning.")
            return True
        else:
            print(f"Template {vm_id} is currently locked. Waiting for it to be unlocked...")
        
        # Wait for the next interval before checking again
        time.sleep(interval)
        total_time += interval
    
    print(f"Template {vm_id} is still locked after {timeout} seconds. Exiting.")
    return False

def wait_for_clone_completion(node, new_vm_id, timeout=300, interval=5):
    """
    Wait for a container clone operation to complete, considering config lock status.
    
    :param node: The Proxmox node name.
    :param new_vm_id: The ID of the new cloned container.
    :param timeout: Total time in seconds to wait for the clone to complete.
    :param interval: Time in seconds between status checks.
    :return: True if clone completed successfully, False if timeout reached.
    """
    total_wait_time = 0
    while total_wait_time < timeout:
        # Check the status of the container
        status = get_proxmox_client().nodes(node).lxc(new_vm_id).status.current().get()
        print(status)
        print(f"Checking status of container {new_vm_id}: {status['status']} (Config: {status.get('lock', 'None')})")

        # If the container is not locked, the cloning operation is complete
        if 'lock' not in status:
            print(f"Container {new_vm_id} clone operation completed successfully.")
            return True

        # If the container is locked for creation, continue waiting
        if status.get('lock') == 'create':
            print(f"Container {new_vm_id} is still being cloned. Waiting...")

        # Wait for the next interval before checking again
        time.sleep(interval)
        total_wait_time += interval

    # If we reach here, the cloning operation did not complete within the timeout
    print(f"Timeout reached while waiting for clone {new_vm_id} to complete.")
    return False


def wait_for_unlock(node, vm_id, timeout=300, interval=5):
    total_time = 0
    while total_time < timeout:
        # Check if the container is locked
        config = get_proxmox_client().nodes(node).lxc(vm_id).status.current().get()
        if 'lock' not in config:
            return True  # Unlocked, proceed with the next step
        print(f"Container {vm_id} is locked, waiting...")
        time.sleep(interval)  # Wait before the next check
        total_time += interval
    raise TimeoutError(f"Container {vm_id} is still locked after {timeout} seconds.")

def check_clone_status(node, vm_id):
    task_status = get_proxmox_client().nodes(node).tasks().get()
    for task in task_status:
        if task['upid'].startswith(f"UPID:{node}:{vm_id}:") and task['status'] == 'running':
            return False
    return True

def start_lxc(node, vm_id):
    get_proxmox_client().nodes(node).lxc(vm_id).status.start().post()

def fetch_lxc_ip(node, vm_id):
    network_info = get_proxmox_client().nodes(node).lxc(vm_id).interfaces().get()
    print(f"network_info: {network_info}")
    print(f"node: {node}")
    print(f"vm_id: {vm_id}")
    if network_info:
        for interface in network_info:
            if interface['name'] == "eth0":
                if 'inet' in interface:
                    return interface['inet'].split('/')[0]

def wait_for_lxc_stop(node, vm_id):
    while True:
        status = get_lxc_status(node, vm_id).get('status')
        if status == "stopped" : return status
        time.sleep(5)

def wait_and_fetch_lxc_ip(node, vm_id):
    while True:
        ip_add = fetch_lxc_ip(node, vm_id)
        if ip_add : return ip_add
        time.sleep(5)