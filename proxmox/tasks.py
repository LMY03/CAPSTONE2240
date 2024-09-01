from celery import shared_task
from django.shortcuts import get_object_or_404
from decouple import config
import logging

from guacamole import guacamole
from proxmox import views, proxmox
from pfsense.views import add_port_forward_rules, delete_port_forward_rules

from .models import VirtualMachines, Nodes
from ticketing.models import RequestEntry, RequestUseCase, PortRules
from guacamole.models import GuacamoleConnection, GuacamoleUser
from django.contrib.auth.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_vm(tsg_user_id, request_id, node):
    # logger.info("===========================")
    tsg_user = User.objects.get(pk=tsg_user_id)
    new_vm_id = views.generate_vm_ids(1)[0]
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    vm_id = int(request_entry.template.vm_id)

    request_use_case = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')[0]

    if request_entry.is_course(): vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
    else: vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"

    if request_entry.get_total_no_of_vm() != 1 : vm_name = f"{vm_name}-Group-1"

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)
    
    vm = VirtualMachines.objects.create(
        vm_id=new_vm_id,
        vm_name=vm_name,
        cores=cpu_cores,
        ram=ram,
        storage=request_entry.template.storage,
        request=request_entry,
        node=get_object_or_404(Nodes, name=node),
    )
    logger.info("===========================")
    upid = proxmox.clone_vm(node, vm_id, new_vm_id, vm_name)
    logger.info(f"upid: {upid}")
    proxmox.wait_for_task(node, upid)
    proxmox.config_vm(node, new_vm_id, cpu_cores, ram)
    proxmox.start_vm(node, new_vm_id)
    ip_add = proxmox.wait_and_get_ip(node, new_vm_id)
    proxmox.shutdown_vm(node, new_vm_id)
    proxmox.wait_for_vm_stop(node, new_vm_id)

    vm.set_ip_add(ip_add)
    vm.set_shutdown()

    protocol = request_entry.template.guacamole_protocol
    port = {
        'vnc': 5901,
        'rdp': 3389,
        'ssh': 22
    }.get(protocol)

    tsg_gaucamole_user = get_object_or_404(GuacamoleUser, system_user=tsg_user)
    guacamole_connection_group_id = guacamole.create_connection_group(f"{request_id}")
    guacamole.assign_connection_group(tsg_gaucamole_user.username, guacamole_connection_group_id)
    guacamole_connection_id = guacamole.create_connection(vm_name, protocol, port, ip_add, config('DEFAULT_VM_USERNAME'), config('DEFAULT_VM_PASSWORD'), guacamole_connection_group_id)
    guacamole.assign_connection(tsg_gaucamole_user.username, guacamole_connection_id)

    # vm = VirtualMachines(
    #     vm_id=new_vm_id, 
    #     vm_name=vm_name, 
    #     cores=cpu_cores, 
    #     ram=ram, 
    #     storage=request_entry.template.storage, 
    #     ip_add=ip_add, 
    #     request=request_entry, 
    #     node=node,
    #     status=VirtualMachines.Status.SHUTDOWN
    # )
    # vm.save()
    GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=tsg_user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection_group_id, vm=vm).save()

def vm_provision(request_id):

    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    vm = get_object_or_404(VirtualMachines, request=request_entry)

    if vm.is_active():

        proxmox.shutdown_vm(vm.node.name, vm.vm_id)

        vm.set_shutdown()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        
    request_use_cases = RequestUseCase.objects.filter(request=request_entry).values('request_use_case', 'vm_count')
    classnames = []
    total_no_of_vm = request_entry.get_total_no_of_vm() - 1
    
    for request_use_case in request_use_cases:
        for i in range(request_use_case['vm_count']):
                if request_entry.is_course(): vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
                else: vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"
                vm_name = f"{vm_name}-Group-{i + 1}"
                classnames.append(vm_name)
    classnames.pop(0)

    cpu_cores = int(request_entry.cores)
    ram = int(request_entry.ram)

    return views.vm_provision_process(vm.vm_id, classnames, total_no_of_vm, cpu_cores, ram, request_id)

@shared_task
def processing_ticket(request_id):

    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    vm_provision(request_id)
    vms = VirtualMachines.objects.filter(request=request_entry)
    port_rules = PortRules.objects.filter(request=request_entry)
    if port_rules.exists():
        protocols = port_rules.values_list('protocol', flat=True)
        local_ports = port_rules.values_list('dest_ports', flat=True)
        ip_adds = vms.values_list('ip_add', flat=True)
        descrs = vms.values_list('vm_name', flat=True)
        add_port_forward_rules(request_id, protocols, local_ports, ip_adds, descrs) # pfsense

@shared_task
def delete_request_process(request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)

    vms = VirtualMachines.objects.filter(request=request_entry)
    port_rules = PortRules.objects.filter(request=request_entry)
    if port_rules.exists() : delete_port_forward_rules(len(port_rules), vms.values_list('vm_name', flat=True)) # pfsense

    for vm in vms:
        if vm.is_active:

            proxmox.stop_vm(vm.node.name, vm.vm_id)

            vm.set_shutdown()

    for vm in vms:
        vm.set_destroyed()

        proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        proxmox.delete_vm(vm.node.name, vm.vm_id)

        guacamole_connection = get_object_or_404(GuacamoleConnection, vm=vm)
        guacamole_connection.is_active = False
        guacamole_connection.save()
        guacamole_user = guacamole_connection.user
        guacamole_user.is_active = False
        guacamole_user.save()

        system_user = guacamole_user.system_user
        system_user.username = f"{system_user.username}_{request_id}"
        system_user.is_active = 0
        system_user.save()
        guacamole.delete_user(guacamole_user.username)
    
    guacamole.delete_connection_group(guacamole_connection.connection_group_id)