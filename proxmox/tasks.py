from celery import shared_task
from django.shortcuts import get_object_or_404
from decouple import config
import logging

from guacamole import guacamole
from guacamole.views import get_port_protocol
from proxmox import views, proxmox
from pfsense.views import add_port_forward_rules, delete_port_forward_rules

from .models import VirtualMachines, Nodes
from ticketing.models import RequestEntry, RequestUseCase, PortRules
from guacamole.models import GuacamoleConnection, GuacamoleUser
from users.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task
def create_test_vm(tsg_user_id, request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    if request_entry.is_pending():
        tsg_user = User.objects.get(pk=tsg_user_id)
        new_vm_id = views.generate_vm_ids(1)[0]
        vm_id = int(request_entry.template.vm_id)

        request_use_case = RequestUseCase.objects.filter(request=request_entry.pk).values('request_use_case', 'vm_count')[0]

        if request_entry.is_course(): vm_name = f"{request_use_case['request_use_case'].replace('_', '-')}"
        else: vm_name = f"{request_entry.get_request_type()}-{request_entry.requester.last_name}-{request_entry.id}"

        vm_name = f"{vm_name}-TestVM"

        cpu_cores = int(request_entry.cores)
        ram = int(request_entry.ram)
        
        #TODO: LOADBALANCING
        node = "pve"

        vm = VirtualMachines.objects.create(
            vm_id=new_vm_id,
            vm_name=vm_name,
            cores=cpu_cores,
            ram=ram,
            storage=request_entry.template.storage,
            request=request_entry,
            node=get_object_or_404(Nodes, name=node),
        )
        # upid = proxmox.clone_vm(node, vm_id, new_vm_id, vm_name)
        # proxmox.wait_for_task(node, upid)
        # proxmox.config_vm(node, new_vm_id, cpu_cores, ram)
        # proxmox.start_vm(node, new_vm_id)
        # ip_add = proxmox.wait_and_get_ip(node, new_vm_id)
        # proxmox.shutdown_vm(node, new_vm_id)
        # proxmox.wait_for_vm_stop(node, new_vm_id)

        ip_add = "10.10.10.10"

        vm.set_ip_add(ip_add)
        vm.set_shutdown()

        protocol = request_entry.template.guacamole_protocol
        port = get_port_protocol(protocol)

        tsg_gaucamole_user = get_object_or_404(GuacamoleUser, system_user=tsg_user)
        guacamole_connection_group_id = guacamole.create_connection_group(f"{request_id}")
        guacamole.assign_connection_group(tsg_gaucamole_user.username, guacamole_connection_group_id)
        guacamole_connection_id = guacamole.create_connection(vm_name, protocol, port, ip_add, config('DEFAULT_VM_USERNAME'), config('DEFAULT_VM_PASSWORD'), guacamole_connection_group_id)
        guacamole.assign_connection(tsg_gaucamole_user.username, guacamole_connection_id)

        GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=tsg_user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection_group_id, vm=vm).save()

        request_entry = get_object_or_404(RequestEntry, pk=request_id)

        request_entry.status = RequestEntry.Status.PROCESSING
        request_entry.assigned_to = tsg_user
        request_entry.save()

def vm_provision(request_id):
    
    # create system_account for test vm
    orig_vm = get_object_or_404(VirtualMachines, request__pk=request_id)
    student_user = User.create_student_user(
        username=orig_vm.vm_name, 
        password=User.objects.make_random_password(),
    )

    guacamole_connection = get_object_or_404(GuacamoleConnection, vm=orig_vm)
    guacamole_connection.user = get_object_or_404(GuacamoleUser, system_user=student_user)
    guacamole_connection.save()

    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    no_of_clone_vm = request_entry.get_total_no_of_vm() - 1
    if no_of_clone_vm > 1:
        # shutdown vm if active
        if orig_vm.is_active():

            # proxmox.shutdown_vm(vm.node.name, vm.vm_id)

            orig_vm.set_shutdown()

            # proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)

        new_vm_ids = []
        node = orig_vm.node.name

        new_vm_ids = views.generate_vm_ids(no_of_clone_vm)

        if orig_vm.is_active():
            proxmox.shutdown_vm(node, orig_vm.vm_id)
            proxmox.wait_for_vm_stop(node, orig_vm.vm_id)
            orig_vm.set_shutdown()

        cpu_cores = int(request_entry.cores)
        ram = int(request_entry.ram)
        
        # generate vm names
        vm_names = views.generate_vm_names(request_id).pop(0)

        upids = []
        for new_vm_id, vm_name in zip(new_vm_ids, vm_names):
            VirtualMachines.objects.create(vm_id=new_vm_id, vm_name=vm_name, cores=cpu_cores, ram=ram, storage=request_entry.template.storage, request=request_entry, node=orig_vm.node)
            upids.append(proxmox.clone_vm(node, vm_id, new_vm_id, vm_name))

        for vm_id, upid in zip(new_vm_ids, upids):
            proxmox.wait_for_task(node, upid)
            proxmox.start_vm(node, vm_id)
        
        hostnames = []
        for vm_id in new_vm_ids:
            proxmox.wait_for_vm_start(node, vm_id)
            hostnames.append(proxmox.wait_and_get_ip(node, vm_id))

        for vm_id in new_vm_ids:
            proxmox.shutdown_vm(node, vm_id)
            proxmox.wait_for_vm_stop(node, vm_id)

        tsg_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username
        faculty_guacamole_username = get_object_or_404(GuacamoleUser, system_user=request_entry.requester).username

        guacamole_connection = get_object_or_404(GuacamoleConnection, vm__pk=vm_id)
        guacamole.assign_connection_group(faculty_guacamole_username, guacamole_connection.connection_group_id)
        guacamole.revoke_connection_group(tsg_guacamole_username, guacamole_connection.connection_group_id)

        guacamole.revoke_connection(tsg_guacamole_username, guacamole_connection.connection_id)
        guacamole.assign_connection(user.username, guacamole_connection.connection_id)
        guacamole.assign_connection(faculty_guacamole_username, guacamole_connection.connection_id)

        vm_username = config('DEFAULT_VM_USERNAME')
        vm_password = config('DEFAULT_VM_PASSWORD')

        # get port protocol
        protocol = request_entry.template.guacamole_protocol
        port = get_port_protocol(protocol)

        for vm_name, hostname in zip(vm_names, hostnames):

            guacamole_connection_id = guacamole.create_connection(vm_name, protocol, port, hostname, vm_username, vm_password, guacamole_connection.connection_group_id)
            guacamole.assign_connection(faculty_guacamole_username, guacamole_connection_id)
            guacamole.assign_connection(vm_name, guacamole_connection_id)

            user = User.create_student_user(
                username=vm_name, 
                password=User.objects.make_random_password(),
            )
            GuacamoleConnection(user=get_object_or_404(GuacamoleUser, system_user=user), connection_id=guacamole_connection_id, connection_group_id=guacamole_connection.connection_group_id, vm=vm).save()

            vm = get_object_or_404(VirtualMachines, vm_name=vm_name, status=VirtualMachines.Status.CREATING)
            vm.set_ip_add(hostname)
            vm.set_shutdown()

    # return views.vm_provision_process(vm.vm_id, classnames, total_no_of_vm, cpu_cores, ram, request_id)

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
    # port_rules = PortRules.objects.filter(request=request_entry)
    # if port_rules.exists() : delete_port_forward_rules(len(port_rules), vms.values_list('vm_name', flat=True)) # pfsense

    for vm in vms:
        if vm.is_active:

            # proxmox.stop_vm(vm.node.name, vm.vm_id)

            vm.set_shutdown()

    for vm in vms:
        vm.set_destroyed()

        # proxmox.wait_for_vm_stop(vm.node.name, vm.vm_id)
        # proxmox.delete_vm(vm.node.name, vm.vm_id)

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