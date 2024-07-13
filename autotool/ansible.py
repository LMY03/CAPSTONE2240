from django.http import JsonResponse
from decouple import config
import ansible_runner
import json
# ansible all -i /ansible/inventory/hosts -m ping -e 'ansible_ssh_common_args="-o StrictHostKeyChecking=no"'

INVENTORY_HOSTS_PATH = '/app/ansible/inventory/hosts'
DEFAULT_VM_USERNAME = config('DEFAULT_VM_USERNAME')
DEFAULT_VM_PASSWORD = config('DEFAULT_VM_PASSWORD')

def change_vm_default_userpass(ip_adds, vm_passwords):

    extra_vars = {
        # 'username': DEFAULT_VM_USERNAME,
        'passwords': vm_passwords,
        'ansible_become_pass': 'DLSU1234!',
    }
    # inventory = "[request]\n"
    inventory = ""
    # if type(ip_adds) is list:
    for ip_add in ip_adds : inventory += f"{ip_add} ansible_user={DEFAULT_VM_USERNAME}\n"
    # elif type(ip_adds) is str:
    #     inventory = f"{ip_adds} ansible_user={DEFAULT_VM_USERNAME}\n"
    return run_playbook('change_vm_pass.yml', inventory, extra_vars)

def resize_vm_disk(ip_add): 
    inventory = f"{ip_add} ansible_user={DEFAULT_VM_USERNAME}\n"

    return run_playbook('change_vm_disk_size.yml', inventory)

def run_playbook(playbook, inventory, extra_vars):
    result = ansible_runner.run(
        private_data_dir='/app/ansible',
        playbook=playbook,
        inventory=inventory,
        extravars=extra_vars
    )

    if result.rc == 0 : return JsonResponse({'status': 'Playbook executed successfully'})
    else:
        return JsonResponse({
            'status': 'Playbook execution failed', 
            'details': result.stdout.read() if result.stdout else 'No output available',
            # 'details': result.stdout.read() if result.stdout else ''
            'message': 'Playbook execution failed'
        })

# def fetch_hosts():
#     hosts_data = [
#         {"ip": "192.168.254.155", "ansible_user": "jin", "hostname": "Node 2", "label": "S12"},
#         {"ip": "192.168.254.156", "ansible_user": "jin", "hostname": "Node 3", "label": "S13"}
#     ]

#     # Start with the group header
#     inventory = "[test]\n"
    
#     # Add each host with its variables inline
#     for host in hosts_data:
#         inventory += f"{host['ip']} ansible_user={host['ansible_user']} hostname={host['hostname']} label={host['label']}\n"

#     return inventory

# def get_inventory(hostname, vm_user, vm_name, label):

#     inventory = "[test]\n"
#     # Add each host with its variables inline
#     for i in range(len(hostname)):
#         inventory += f"{hostname[i]} ansible_user={vm_user[i]} hostname={vm_name[i]} label={label[i]}\n"

#     return inventory

# def run_playbook(playbook, hostname, vm_user, vm_name, label):
#     inventory = get_inventory(hostname, vm_user, vm_name, label)
#     result = ansible_runner.run(
#         private_data_dir='/app/ansible',
#         playbook=playbook,
#         inventory=inventory,
#         extravars={"ansible_become_pass": "123456"}
#     )

#     if result.rc == 0:
#         return JsonResponse({'status': 'Playbook executed successfully'})
#     else:
#         return JsonResponse({
#             'status': 'Playbook execution failed', 
#             'details': result.stdout.read() if result.stdout else 'No output available',
#             # 'details': result.stdout.read() if result.stdout else ''
#             'message': 'Playbook execution failed'
#         })


# def run_playbook():

#     # Define your dynamic host variables
#     hosts = [
#         {
#             "host": "192.168.254.151",
#             "hostname": "Node 1",
#             "label": "S11"
#         },
#         {
#             "host": "192.168.254.152",
#             "hostname": "Node 2",
#             "label": "S12"
#         }
#     ]

#     # Setup Jinja2 environment
#     env = Environment(loader=FileSystemLoader('/app/ansible/project/templates'))
#     template = env.get_template('netdata_config.yml.j2')

#     # Render the playbook content with dynamic values
#     playbook_content = template.render(hosts=hosts)

#     # Define private_data_dir and create directory structure
#     private_data_dir = '/app/ansible'
#     os.makedirs(f"{private_data_dir}/project", exist_ok=True)
#     os.makedirs(f"{private_data_dir}/inventory", exist_ok=True)

#     # Write the rendered playbook to the project directory
#     playbook_path = f'{private_data_dir}/project/playbook.yml'
#     with open(playbook_path, 'w') as playbook_file:
#         playbook_file.write(playbook_content)

#     # Create the inventory file
#     inventory_content = """
#     [all]
#     192.168.254.151
#     192.168.254.152
#     """
#     inventory_path = f'{private_data_dir}/inventory/hosts'
#     with open(inventory_path, 'w') as inventory_file:
#         inventory_file.write(inventory_content)

#     # Run the playbook using ansible-runner
#     result = ansible_runner.run(
#         private_data_dir=private_data_dir,
#         playbook='playbook.yml',
#         inventory='inventory/hosts'
#     )

#     # Check the result
#     if result.rc == 0:
#         return JsonResponse({'status': 'Playbook executed successfully'})
#     else:
#         return JsonResponse({
#             'status': 'Playbook execution failed', 
#             'details': result.stdout.read() if result.stdout else ''
#         })

# def run_command(command): 
#     print(command)
#     try:
#         result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         output = result.stdout.decode() + "\n" + result.stderr.decode()
#     except subprocess.CalledProcessError as e:
#         output = f"Command failed with error code {e.returncode}: {e.output.decode()}"
    
#     return HttpResponse(output, content_type="text/plain")
    
# def run_playbook(playbook):
#     run_command("ansible-playbook -i " + INVENTORY_HOSTS_PATH + " /app/ansible/playbooks/" + playbook + ".yml")
    
# def check_playbook(playbook):
#     run_command("ansible-playbook --check " + playbook + ".yml")

# def run_ansible_lint(playbook):
#     run_command("ansible-lint --check " + playbook + ".yml")

# def test_ping():
#     run_command("ansible all -i " + INVENTORY_HOSTS_PATH + "")