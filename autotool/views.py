from django.shortcuts import render
from decouple import config

from . import ansible
from proxmox import proxmox

# Create your views here.

def renders(request) : 
    return render(request, "ansible.html")

# Create Inventory Hosts File by request
# Generate Json Data for ansible playbook
# Run playbook

def run(request):
    if request.method == "POST":
        node = "pve"
        vm_id = 1000
        proxmox.get_vm_ip(node, vm_id)
        response = ansible.resize_vm_disk(node, vm_id, proxmox.get_vm_ip(node, vm_id))

        return render(request, "data.html", { "data" : response })

# def run_ansible_playbook():
#     try:
#         # command = "docker exec ansible_service ansible-playbook /playbooks/playbook.yml"
#         command = "docker exec -it ansible ansible all -i /inventory/hosts -m ping"
#         result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
#         return result.stdout.decode()
#     except subprocess.CalledProcessError as e:
#         return str(e)
    
# def run_ansible_playbook(playbook):
#     return run_command("ansible-playbook " + "/playbooks/" + playbook + ".yml")



# def run_playbook():
#     playbook_path = '/playbooks/playbook.yml'
#     inventory_path = '/inventory/hosts'

#     r = ansible_runner.run(private_data_dir='/tmp/', playbook=playbook_path, inventory=inventory_path)

#     if r.status == 'successful':
#         return JsonResponse({'status': 'success', 'data': r.get_fact_cache()})
#     else:
#         return JsonResponse({'status': 'failure', 'data': r.stderr})