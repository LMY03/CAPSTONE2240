from django.shortcuts import render

from . import ansible

# Create your views here.

def renders(request) : 
    return render(request, "ansible.html")

# Create Inventory Hosts File by request
# Generate Json Data for ansible playbook
# Run playbook

def run(request):
    if request.method == "POST":

        data = request.POST
        # command = data.get("command")
        # ip_add = data.get("ip_add")

        # vm_user = "jin"
        # ansible.update_inventory_hosts(ip_add, vm_user)

        # ansible.run_command(command)
        # response = ansible.run_playbook(command)
        # ansible.update_inventory_hosts()
        # response = ansible.run_playbook()
        playbook = "netdata_conf.yml"
        no_of_vm = 2
        classname = "Test"
        hostname = ["192.168.254.155", "192.168.254.156"]
        vm_user = []
        vm_name = []
        label = []

        for i in range(no_of_vm):
            vm_user.append("jin")
            vm_name.append(classname + "-" + str(i))
            label.append(classname)
        response = ansible.run_playbook(playbook, hostname, vm_user, vm_name, label)

        return render(request, "data.html", { "data" : response })

def get_ansible_variables():
    data = list()

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