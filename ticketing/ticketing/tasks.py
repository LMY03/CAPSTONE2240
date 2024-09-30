from celery import shared_task
from django.utils import timezone
from django.shortcuts import get_object_or_404

from guacamole import guacamole
from proxmox import proxmox
from pfsense.views import delete_port_forward_rules

from .models import RequestEntry
from guacamole.models import GuacamoleConnection
from proxmox.models import VirtualMachines
from pfsense.models import PortRules

@shared_task
def delete_expired_requests():
    request_entries = RequestEntry.objects.filter(status=RequestEntry.Status.ONGOING)
    for request_entry in request_entries:
        if timezone.localdate() == request_entry.expiration_date:
            delete_request(request_entry.pk)

@shared_task
def delete_request(request_id):
    request_entry = get_object_or_404(RequestEntry, pk=request_id)
    request_entry.status = RequestEntry.Status.DELETED
    request_entry.save()

    vms = VirtualMachines.objects.filter(request=request_entry)
    port_rules = PortRules.objects.filter(request=request_entry)
    if port_rules.exists() : delete_port_forward_rules(len(port_rules), vms.values_list('vm_name', flat=True)) # pfsense

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
