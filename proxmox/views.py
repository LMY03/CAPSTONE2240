from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from decouple import config

import secrets, string

from guacamole import guacamole
from . import proxmox

from . models import VirtualMachines, VMTemplates
from ticketing.models import RequestEntry, RequestUseCase
from guacamole.models import GuacamoleConnection, GuacamoleUser
from pfsense.models import DestinationPorts

from django.contrib.auth.models import User

# Create your views here.

@login_required
def vm_list(request):
    if request.user.is_faculty() : return faculty_vm_list(request)
    elif request.user.is_tsg() : return tsg_vm_list(request)
    else : return redirect('/')

def faculty_vm_list(request):
    request_entries = RequestEntry.objects.filter(requester=request.user, vm_date_tested__isnull=False).exclude(status=RequestEntry.Status.DELETED).order_by('-id')
    
    vm_list = []
    for request_entry in request_entries: 
        vm_list += VirtualMachines.objects.filter(request=request_entry).exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).exclude(is_lxc=True)

    return render(request, 'proxmox/faculty_vm_list.html', { 'vm_list': vm_list })
    
def tsg_vm_list(request):
    return render(request, 'proxmox/tsg_vm_list.html', { 'vm_list': list(VirtualMachines.objects.all().exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).exclude(is_lxc=True)) })

@login_required
def vm_details(request, vm_id):
    if request.user.is_faculty() : return faculty_vm_details(request, vm_id)
    elif request.user.is_tsg() : return tsg_vm_details(request, vm_id)
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

def generate_vm_names(request_id):
    vm_names = []
    request_entry = get_object_or_404(RequestEntry, request__id=request_id)
    request_use_cases = RequestUseCase.objects.filter(request=request_entry).values('request_use_case', 'vm_count')
    for request_use_case in request_use_cases:
        for i in range(request_use_case['vm_count']):
                if request_entry.is_course(): 
                    vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
                else: 
                    vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"

                vm_name = f"{vm_name}-Group-{i + 1}"
                vm_names.append(vm_name)

    return vm_names

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