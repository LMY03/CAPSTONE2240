from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

import secrets, string

from guacamole import guacamole
#from autotool import ansible
from . import proxmox
from . models import VirtualMachines, VMUser
from ticketing.models import VMTemplates, UserProfile
from guacamole.models import GuacamoleConnection, GuacamoleUser
from django.contrib.auth.models import User

from ticketing.models import RequestEntry, UserProfile

# Create your views here.

@login_required
def vm_list(request):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_vm_list(request)
    elif user_role == 'admin' : return tsg_vm_list(request)
    else : return redirect('/')

def faculty_vm_list(request):
    request_entries = RequestEntry.objects.filter(requester=request.user).exclude(is_vm_tested=False).order_by('-id')
    
    vm_list = []
    for request_entry in request_entries : vm_list += VirtualMachines.objects.filter(request=request_entry).exclude(is_lxc=True).exclude(status=VirtualMachines.Status.DESTROYED)

    return render(request, 'proxmox/faculty_vm_list.html', { 'vm_list': vm_list })
    
def tsg_vm_list(request):
    return render(request, 'proxmox/tsg_vm_list.html', { 'vm_list': list(VirtualMachines.objects.all().exclude(status=VirtualMachines.Status.DESTROYED).exclude(is_lxc=True)) })

@login_required
def vm_details(request, vm_id):
    user_role = get_object_or_404(UserProfile, user=request.user).user_type
    if user_role == 'faculty' : return faculty_vm_details(request, vm_id)
    elif user_role == 'admin' : return tsg_vm_details(request, vm_id)
    else : return redirect('/')

def faculty_vm_details(request, vm_id):
    return render(request, 'proxmox/faculty_vm_details.html', { 'vm': get_object_or_404(VirtualMachines, id=vm_id) })
    
def tsg_vm_details(request, vm_id):
    return render(request, 'proxmox/tsg_vm_details.html', { 'vm': get_object_or_404(VirtualMachines, id=vm_id) })


def generate_vm_ids(no_of_vm):
    
    existing_ids = VirtualMachines.objects.exclude(status=VirtualMachines.Status.DESTROYED)

    new_ids = []
    new_id = 10000  # Starting point for new VM IDs
    while len(new_ids) < no_of_vm:
        if new_id not in existing_ids:
            new_ids.append(new_id)
        new_id += 1

    return new_ids

def vm_provision_process(node, vm_id, classnames, no_of_vm, cpu_cores, ram, request_id):

    # vm_temp = get_object_or_404(VMTemplates, vm_id=vm_id)

    orig_vm = get_object_or_404(VirtualMachines, id=vm_id)

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

    new_vm_ids = generate_vm_ids(no_of_vm)

    # for i in range(no_of_vm):
    #     upids.append(proxmox.clone_vm(node, vm_id, new_vm_ids[i], classnames[i])['data'])

    # for i in range(no_of_vm):
    #     # wait for vm to clone
    #     proxmox.wait_for_task(node, upids[i])
    #     # change vm configuration
    #     proxmox.config_vm(node, new_vm_ids[i], cpu_cores, ram)
    #     # start vm
    #     proxmox.start_vm(node, new_vm_ids[i])

    # vm_user = get_object_or_404(VMUser, vm__vm_id=vm_id)
    # username = vm_user.username
    # password = vm_user.password

    username = "jin"
    password = "123456"
    
    request_entry = get_object_or_404(RequestEntry, id=request_id)
    requester = request_entry.requester
    faculty_guacamole_user = get_object_or_404(GuacamoleUser, system_user=requester)
    faculty_guacamole_username = faculty_guacamole_user.username
    guacamole_connection_group_id = get_object_or_404(GuacamoleConnection, vm=orig_vm).connection_group_id
    
    for i in range(no_of_vm):
        # wait for vm to start
        # proxmox.wait_for_vm_start(node, new_vm_ids[i])
        # hostnames.append(proxmox.wait_and_get_ip(node, new_vm_ids[i]))
        # proxmox.shutdown_vm(node, new_vm_ids[i])

        hostnames.append("10.10.10." + str(i))
        
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
        
        print("new_id = " + str(new_vm_ids[i]))
        vm = VirtualMachines(request=request_entry, vm_id=new_vm_ids[i], vm_name=classnames[i], cores=cpu_cores, ram=ram, storage=request_entry.template.storage, ip_add=hostnames[i], node=node, status=VirtualMachines.Status.SHUTDOWN)
        vm.save()
        GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=user), connection_id=guacamole_connection_ids[i], connection_group_id=guacamole_connection_group_id, vm=vm).save()
        VMUser.objects.create(vm=vm, username=username, password=password)

    # set hostnames and label in netdata
    vm_users = []
    labels = []
    credentials = []
    for i in range(no_of_vm):
        vm_users.append("jin")
        labels.append(classnames[i])

        # password = generate_secure_random_string(15)
        # User.objects.create_user(username=classnames[i], password=password)
        # password = generate_secure_random_string(15)
        # User.objects.create_user(username=classnames[i], password=password)

        credentials.append({'username': classnames[i], 'password': password})
        # Create System Users
        # classname[i] is the username

    # ansible.run_playbook("netdata_conf.yml", hostnames, vm_users, classnames, labels)

    return {
        'username' : classnames,
        'passwords' : passwords,
        # 'vm_user': ,
        # 'vm_pass': ,
    }

def shutdown_vm(request, vm_id):

    vm = get_object_or_404(VirtualMachines, id=vm_id)

    if vm.status == VirtualMachines.Status.ACTIVE:
        
        # proxmox.shutdown_vm(vm.node, vm.vm_id)

        vm.status = vm.Status.SHUTDOWN
        vm.save()

        return redirect("/users/student/vm/" + vm_id)

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