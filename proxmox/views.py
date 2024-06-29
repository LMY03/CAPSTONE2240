import time, secrets, string

from django.shortcuts import get_object_or_404, redirect, render

from guacamole import guacamole
#from autotool import ansible
from . import proxmox
from . models import VirtualMachines, VMUser
from ticketing.models import VMTemplates, UserProfile
from guacamole.models import GuacamoleConnection, GuacamoleUser
from django.contrib.auth.models import User

from ticketing.models import RequestEntry, UserProfile

# Create your views here.

def vm_provision_process(node, vm_id, classnames, no_of_vm, cpu_cores, ram, request_id):

    vm_temp = get_object_or_404(VMTemplates, vm_id=vm_id)

    protocol = "rdp"
    port = {
        'vnc': 5901,
        'rdp': 3389,
        'ssh': 22
    }.get(protocol)

    upids = []
    new_vm_ids = []
    hostnames = []
    guacamole_connection_ids = []
    passwords = []

    for i in range(no_of_vm):
        # TODO : CREATE ALGO TO ASSIGN VM_IDS
        new_vm_ids.append(vm_id + i + 1)
        upids.append(proxmox.clone_vm(node, vm_id, new_vm_ids[i], classnames[i])['data'])

    for i in range(no_of_vm):
        # wait for vm to clone
        proxmox.wait_for_task(node, upids[i])
        # change vm configuration
        proxmox.config_vm(node, new_vm_ids[i], cpu_cores, ram)
        # start vm
        proxmox.start_vm(node, new_vm_ids[i])

    # vm_user = get_object_or_404(VMUser, vm__vm_id=vm_id)
    # username = vm_user.username
    # password = vm_user.password

    username = "jin"
    password = "123456"
    
    requester = RequestEntry.objects.get(id=request_id).requester
    faculty_guacamole_user = GuacamoleUser.objects.get(system_user=requester)
    faculty_guacamole_username = faculty_guacamole_user.username
    guacamole_connection_group_id = guacamole.create_connection_group(f"{request_id}")
    
    for i in range(no_of_vm):
        # wait for vm to start
        proxmox.wait_for_vm_start(node, new_vm_ids[i])
        hostnames.append(proxmox.wait_and_get_ip(node, new_vm_ids[i]))

        # hostnames.append("10.10.10." + str(i))
        # hostnames.append("172.20.10.5")
        
        # create connection
        guacamole_connection_ids.append(guacamole.create_connection(classnames[i], protocol, port, hostnames[i], username, password, guacamole_connection_group_id))
        # Create System User
        passwords.append(User.objects.make_random_password())
        # passwords.append("123456")
        user = User(username=classnames[i])
        user.set_password(passwords[i])
        user.save()
        UserProfile.objects.create(user=user)
        guacamole.assign_connection(classnames[i], guacamole_connection_ids[i])
        guacamole.assign_connection(faculty_guacamole_username, guacamole_connection_ids[i])
        vm = VirtualMachines(request_id=request_id, vm_id=new_vm_ids[i], vm_name=classnames[i], cores=cpu_cores, ram=ram, storage=vm_temp.storage, ip_add=hostnames[i], node=node, status=VirtualMachines.Status.ACTIVE)
        vm.save()
        GuacamoleConnection(user=GuacamoleUser.objects.get(system_user=user), connection_id=guacamole_connection_ids[i], connection_group_id=guacamole_connection_group_id, vm=vm).save()
        VMUser.objects.create(vm=vm, username=username, password=password)

    guacamole.assign_connection_group(faculty_guacamole_username, guacamole_connection_group_id)
    # set hostnames and label in netdata
    vm_users = []
    labels = []
    credentials = []
    for i in range(no_of_vm):
        vm_users.append("jin")
        labels.append(classnames[i])

        # password = generate_secure_random_string(15)
        # User.objects.create_user(username=classnames[i], password=password)

        credentials.append({'username': classnames[i], 'password': password})
        # Create System Users
        # classname[i] is the username

    # ansible.run_playbook("netdata_conf.yml", hostnames, vm_users, classnames, labels)

    return {
        'vm_id' : new_vm_ids, 
        'guacamole_connection_id' : guacamole_connection_ids,
        'username' : classnames,
        'passwords' : passwords,
    }

def shutdown_vm(request):
    if request.method == "POST":
        
        data = request.POST
        vm_id = data.get("vm_id")

        vm = get_object_or_404(VirtualMachines, id=vm_id)
        print("start vm -------------------------")
        print(vm)

        if vm.status == VirtualMachines.Status.ACTIVE:
            
            proxmox.shutdown_vm(vm.node, vm_id)

            vm.status = vm.Status.SHUTDOWN
            vm.save()

            return redirect("/users/student/vm/" + vm_id)

node = "pve"

def renders(request) : 
    return render(request, "proxmox.html")

def clone_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        new_vm_id = data.get("newid")

        response = proxmox.clone_vm(node, vmid, new_vm_id, "ITDBADM-S15-Group-1")

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def start_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.start_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def shutdown_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.shutdown_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def delete_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.delete_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def stop_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.stop_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def status_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        status = proxmox.get_vm_status(node, vmid)

        return render(request, "data.html", { "data" : status })
        
    return redirect("/proxmox")

def ip_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        ip = proxmox.get_vm_ip(node, vmid)

        return render(request, "data.html", { "data" : ip })
        
    return redirect("/proxmox")

def config_vm(request) : 

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        cpu_cores = data.get("cpu")
        memory = data.get("memory")

        response = proxmox.config_vm(node, vmid, cpu_cores, memory)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/proxmox")

def clone_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        new_vm_id = data.get("newid")

        response = proxmox.clone_lxc(node, vmid, new_vm_id)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def start_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.start_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def shutdown_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.shutdown_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def delete_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.delete_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def stop_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.stop_lxc(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

def status_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        status = proxmox.get_lxc_status(node, vmid)# [status]

        return render(request, "data.html", { "data" : status })
        
    return redirect("/proxmox")

def ip_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        ip = proxmox.wait_and_get_lxc_ip(node, vmid)

        return render(request, "data.html", { "data" : ip })
        
    return redirect("/proxmox")

def config_lxc(request) : 

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        cpu_cores = data.get("cpu")
        memory = data.get("memory")

        response = proxmox.config_lxc(node, vmid, cpu_cores, memory)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/proxmox")

def generate_secure_random_string(length):
    letters = string.ascii_letters + string.digits
    result_str = ''.join(secrets.choice(letters) for i in range(length))
    return result_str