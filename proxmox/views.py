from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from decouple import config

import secrets, string

from guacamole import guacamole
from autotool import ansible
from . import proxmox

from . models import VirtualMachines
from ticketing.models import RequestEntry, UserProfile, VMTemplates
from guacamole.models import GuacamoleConnection, GuacamoleUser
from pfsense.models import DestinationPorts

from django.contrib.auth.models import User

# Create your views here.

@login_required
def vm_list(request):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_vm_list(request)
    elif user_role == 'admin' : return tsg_vm_list(request)
    else : return redirect('/')

def faculty_vm_list(request):
    request_entries = RequestEntry.objects.filter(requester=request.user, is_vm_tested=True).exclude(status=RequestEntry.Status.DELETED).order_by('-id')
    
    vm_list = []
    for request_entry in request_entries: 
        vm_list += VirtualMachines.objects.filter(request=request_entry).exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).exclude(is_lxc=True)

    return render(request, 'proxmox/faculty_vm_list.html', { 'vm_list': vm_list })
    
def tsg_vm_list(request):
    return render(request, 'proxmox/tsg_vm_list.html', { 'vm_list': list(VirtualMachines.objects.all().exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).exclude(is_lxc=True)) })

@login_required
def vm_details(request, vm_id):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_vm_details(request, vm_id)
    elif user_role == 'admin' : return tsg_vm_details(request, vm_id)
    else : return redirect('/')

def faculty_vm_details(request, vm_id):
    vm = get_object_or_404(VirtualMachines, id=vm_id)
    context = {
        'vm': get_object_or_404(VirtualMachines, id=vm_id),
        'destination_ports': DestinationPorts.objects.filter(vm=vm)
    }
    return render(request, 'proxmox/faculty_vm_details.html', context)
    
def tsg_vm_details(request, vm_id):
    vm = get_object_or_404(VirtualMachines, id=vm_id)
    context = {
        'vm': get_object_or_404(VirtualMachines, id=vm_id),
        'destination_ports': DestinationPorts.objects.filter(vm=vm)
    }
    return render(request, 'proxmox/tsg_vm_details.html', context)

def generate_vm_ids(no_of_vm):
    
    existing_vms = set(VirtualMachines.objects.exclude(status=VirtualMachines.Status.DESTROYED).values_list('vm_id', flat=True))

    new_ids = []
    new_id = 10000  # Starting point for new VM IDs
    while len(new_ids) < no_of_vm:
        if new_id not in existing_vms : new_ids.append(new_id)
        new_id += 1

    return new_ids

def vm_provision_process(vm_id, classnames, no_of_vm, cpu_cores, ram, request_id):

    request_entry = get_object_or_404(RequestEntry, id=request_id)
    orig_vm = get_object_or_404(VirtualMachines, vm_id=vm_id, request_id=request_id)
    guacamole_connection = get_object_or_404(GuacamoleConnection, vm=orig_vm)
    password = User.objects.make_random_password()
    orig_vm.system_password = password
    orig_vm.save()
    
    user = User(username=orig_vm.vm_name)
    user.set_password(password)
    user.save()
    UserProfile.objects.create(user=user)
    guacamole_connection.user = get_object_or_404(GuacamoleUser, system_user=user)
    guacamole_connection.save()

    node = orig_vm.node.name
    protocol = request_entry.template.guacamole_protocol
    port = {
        'vnc': 5901,
        'rdp': 3389,
        'ssh': 22
    }.get(protocol)

    upids = []
    new_vm_ids = []
    hostnames = []
    passwords = []
    vm_passwords = []

    new_vm_ids = generate_vm_ids(no_of_vm)
    orig_vm_password = User.objects.make_random_password()
    vm_passwords.append(orig_vm_password)
    # guacamole.update_connection() # change ip of original vm

    if orig_vm.is_active():
        proxmox.shutdown_vm(node, orig_vm.vm_id)
        proxmox.wait_for_vm_stop(node, orig_vm.vm_id)
        orig_vm.set_shutdown()


    for new_vm_id, vm_name in zip(new_vm_ids, classnames):
        password = User.objects.make_random_password()
        passwords.append(password)
        VirtualMachines.objects.create(vm_id=new_vm_id, vm_name=vm_name, cores=cpu_cores, ram=ram, storage=request_entry.template.storage, request=request_entry, node=orig_vm.node, system_password=password)
        upids.append(proxmox.clone_vm(node, vm_id, new_vm_id, vm_name))

    for vm_id, upid in zip(new_vm_ids, upids):
        proxmox.wait_for_task(node, upid)
        proxmox.start_vm(node, vm_id)

    tsg_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
    faculty_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username

    guacamole.assign_connection_group(faculty_guacamole_username, guacamole_connection.connection_group_id)
    guacamole.revoke_connection_group(tsg_guacamole_username, guacamole_connection.connection_group_id)

    guacamole.revoke_connection(tsg_guacamole_username, guacamole_connection.connection_id)
    guacamole.assign_connection(user.username, guacamole_connection.connection_id)
    guacamole.assign_connection(faculty_guacamole_username, guacamole_connection.connection_id)
    
    vms = []
    vms.append(orig_vm)
    proxmox.start_vm(node, orig_vm.vm_id)
    for vm_id in new_vm_ids:
        proxmox.wait_for_vm_start(node, vm_id)
        hostnames.append(proxmox.wait_and_get_ip(node, vm_id))
        vm_password = User.objects.make_random_password()
        vm_passwords.append(vm_password)

        # hostnames.append("10.10.10." + str(vm_id))

    # orig_vm.ip_add = "10.10.10.10"
    orig_vm.ip_add =  proxmox.wait_and_get_ip(node, orig_vm.vm_id)
    orig_vm.save()
    hostnames.insert(0, orig_vm.ip_add)

    proxmox.shutdown_vm(node, orig_vm.vm_id)

    for vm_id in new_vm_ids:
        proxmox.shutdown_vm(node, vm_id)
        proxmox.wait_for_vm_stop(node, vm_id)

    vm_username = config('DEFAULT_VM_USERNAME')

    for i in range(no_of_vm):
        # passwords.append(User.objects.make_random_password())
        user = User(username=classnames[i])
        user.set_password(passwords[i])
        user.save()
        UserProfile.objects.create(user=user)

        # guacamole_connection_ids.append(guacamole.create_connection(classnames[i], protocol, port, hostnames[i], vm_username, passwords[i], guacamole_connection_group_id))
        # guacamole_connection_id = guacamole.create_connection(classnames[i], protocol, port, hostnames[i+1], vm_username, vm_passwords[i+1], guacamole_connection.connection_group_id)
        guacamole_connection_id = guacamole.create_connection(classnames[i], protocol, port, hostnames[i], vm_username, "DLSU1234!", guacamole_connection.connection_group_id)
        guacamole.assign_connection(classnames[i], guacamole_connection_id)
        guacamole.assign_connection(faculty_guacamole_username, guacamole_connection_id)
        
        # vm = VirtualMachines(request=request_entry, vm_id=new_vm_ids[i], vm_name=classnames[i], cores=cpu_cores, ram=ram, storage=request_entry.template.storage, ip_add=hostnames[i], node=orig_vm.node, status=VirtualMachines.Status.SHUTDOWN)
        vm = get_object_or_404(VirtualMachines, vm_name=classnames[i], status=VirtualMachines.Status.CREATING)
        vm.set_ip_add(hostnames[i])
        vm.set_shutdown()
        vms.append(vm)
        GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection.connection_group_id, vm=vm).save()

    # orig_vm.vm_password = User.objects.make_random_password()
    passwords.insert(0, password)
    classnames.insert(0, orig_vm.vm_name)

    return {
        'usernames' : classnames,
        'passwords' : passwords,
        # 'vm_passs': vm_passwords,
    }

def shutdown_vm(request, vm_id):

    vm = get_object_or_404(VirtualMachines, id=vm_id)

    if vm.is_active():
        
        proxmox.shutdown_vm(vm.node.name, vm.vm_id)

        vm.set_shutdown()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)

    return redirect(request.META.get('HTTP_REFERER'))

def get_vm_ip_adds(request_id):
    return list(VirtualMachines.objects.filter(request_id=request_id).values_list('ip_add', flat=True))

def get_vm_userpass(request_id):
    vm_userpass = {'username': [], 'password': []}
    vms = VirtualMachines.objects.filter(request_id=request_id).order_by('id')
    for vm in vms:
        vm_userpass['username'].append(vm.get_vm_userpass()['username'])
        vm_userpass['password'].append(vm.get_vm_userpass()['password'])
    return vm_userpass

# def lxc_provision(): 
#     node = "pve"
#     vmid = 2240
#     snapname = "CAP-2240-Snapshot"
#     ostemplate = "local:vztmpl/debian-11-standard_11.0-1_amd64.tar.gz"
#     storage = "local-lvm"
#     hostname_prefix = "new-container-"

#     # Step 1: Create a snapshot
#     snapshot_response = create_snapshot(node, vmid, snapname)
#     print("Snapshot response:", snapshot_response)

#     # Check if snapshot was created successfully
#     if snapshot_response.get("data"):
#         # Step 2: Create multiple containers and restore the snapshot
#         for i in range(1, 6):  # Adjust the range for the number of containers you need
#             new_vmid = 101 + i
#             hostname = f"{hostname_prefix}{i}"
            
#             # Create new container
#             create_container_response = create_container(node, new_vmid, ostemplate, storage, hostname)
#             print(f"Create container {new_vmid} response:", create_container_response)
            
#             # Wait for the container to be created
#             time.sleep(10)  # Adjust sleep time based on your Proxmox server's performance
            
#             # Restore snapshot to the new container
#             restore_response = restore_snapshot_to_container(node, new_vmid, vmid, snapname)
#             print(f"Restore snapshot to container {new_vmid} response:", restore_response)
            
#             # Wait a bit before creating the next container
#             time.sleep(10)  # Adjust sleep time as needed
#     else:
#         print("Failed to create snapshot.")

node = "pve"

def renders(request) : 
    return render(request, "proxmox.html")

def clone_vm(request) :

    if request.method == "POST":

        data = request.POST
        vm_id = data.get("vmid")
        new_vm_id = data.get("newid")

        response = proxmox.clone_vm(node, vm_id, new_vm_id, "ITDBADM-S15-Group-1")
        proxmox.wait_for_task(node, response)
        proxmox.config_vm(node, new_vm_id, 2, 2048)
        proxmox.start_vm(node, new_vm_id)
        ip_add = proxmox.wait_and_get_ip(node, new_vm_id)
        proxmox.shutdown_vm(node, new_vm_id)

        return render(request, "data.html", { "data" : ip_add })
        
    return redirect("/proxmox")

def start_vm(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")

        response = proxmox.start_vm(node, vmid)

        return render(request, "data.html", { "data" : response })
        
    return redirect("/proxmox")

# def shutdown_vm(request) :

#     if request.method == "POST":

#         data = request.POST
#         vmid = data.get("vmid")

#         response = proxmox.shutdown_vm(node, vmid)

#         return render(request, "data.html", { "data" : response })
        
#     return redirect("/proxmox")

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

def config_vm_disk(request) : 

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        size = data.get("size")

        response = proxmox.config_vm_disk(node, vmid, size)

        return render(request, "data.html", { "data" : response })
    
    return redirect("/vm")

def create_lxc(request) :

    if request.method == "POST":

        data = request.POST
        vmid = data.get("vmid")
        ostemplate = "local:vztmpl/ubuntu-23.10-1_amd64.tar.zst"

        response = proxmox.create_lxc(node, ostemplate, vmid, 1, 1024, 'local-lvm')

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

def get_templates(request) : 
    return render(request, "data.html", { "data" : proxmox.get_templates("pve") })

def generate_secure_random_string(length):
    letters = string.ascii_letters + string.digits
    result_str = ''.join(secrets.choice(letters) for i in range(length))
    return result_str

def accept_vm (request, vm_id):
    return (request, 'users:faculty_request_list')