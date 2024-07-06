from django.shortcuts import render

from . import ansible
from ticketing.models import RequestEntry

# Create your views here.

def renders(request) : 
    return render(request, "ansible.html")

# Create Inventory Hosts File by request
# Generate Json Data for ansible playbook
# Run playbook

def run(request):
    if request.method == "POST":

        data = request.POST
        playbook = "netdata_conf.yml"
        no_of_vm = 2
        classname = "Test"
        hostname = ["192.168.1.17", "192.168.1.18"]
        vm_passwords = ['password1', 'password2']
        response = ansible.change_vm_default_userpass(16, vm_passwords)

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