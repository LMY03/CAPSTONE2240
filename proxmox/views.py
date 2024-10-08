from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from decouple import config

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
    vm_list = VirtualMachines.objects.filter(
        request__in=RequestEntry.objects.filter(
            requester=request.user, 
            vm_date_tested__isnull=False, 
            # template__is_lxc=False
        ).exclude(status=RequestEntry.Status.DELETED)
    ).exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).order_by('-request__id')

    return render(request, 'proxmox/faculty_vm_list.html', { 'vm_list': vm_list })
    
def tsg_vm_list(request):

    vm_list = VirtualMachines.objects.filter(
        request__in=RequestEntry.objects.filter(
            assigned_to=request.user, 
            # template__is_lxc=False
        )
    ).exclude(status=VirtualMachines.Status.DESTROYED).exclude(status=VirtualMachines.Status.CREATING).order_by('-request__id')

    return render(request, 'proxmox/tsg_vm_list.html', { 'vm_list': vm_list })

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
    new_id = 5000  # Starting point for new VM IDs
    while len(new_ids) < no_of_vm:
        if new_id not in existing_vms : new_ids.append(new_id)
        new_id += 1

    return new_ids

def generate_vm_names(request_entry : RequestEntry):
    vm_names = []
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

def shutdown_vm(vm : VirtualMachines):

    if vm.is_active():
        
        if not vm.is_lxc():
            
            proxmox.shutdown_vm(vm.node.name, vm.vm_id)

            vm.set_shutdown()

            proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        else:
            
            proxmox.shutdown_lxc(vm.node.name, vm.vm_id)

            vm.set_shutdown()

            proxmox.wait_for_lxc_stop(vm.node.name, vm.vm_id)

def perform_shutdown(request, vm_id):

    shutdown_vm(get_object_or_404(VirtualMachines, vm_id=vm_id))

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

def get_node_to_clone_vms():
    return "pve"