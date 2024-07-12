from django.shortcuts import get_object_or_404
import time, random

from . import pfsense

from . models import DestinationPorts
from ticketing.models import RequestEntry, PortRules

# Create your views here.

def get_port_forward_rule(vm_name, token):
    rules = pfsense.get_port_forward_rules(token)
    for rule in rules:
        if rule['descr'] == vm_name: return rule['id']

def get_firewall_rule(vm_name, token):
    rules = pfsense.get_firewall_rules(token)
    for rule in rules:
        if rule['descr'] == vm_name : return rule['id']

def generate_dest_ports(no_of_ports_needed):

    used_ports = DestinationPorts.objects.filter(
        port_rule__request__status=RequestEntry.Status.ONGOING
    ).values_list('dest_port', flat=True)

    used_ports_set = set(map(int, used_ports))

    # Define the range of dynamic/private ports
    all_ports = set(range(49152, 65536))
    available_ports = all_ports - used_ports_set

    # if len(available_ports) < no_of_ports_needed:
    #     raise ValueError("Not enough available ports to satisfy the request.")

    selected_ports = random.sample(available_ports, no_of_ports_needed)
    return selected_ports

def add_port_forward_rules(request_id, protocols, local_ports, ip_adds, descrs):

    if isinstance(protocols, str): protocols = [protocols]
    if isinstance(local_ports, str): local_ports = [local_ports]
    if isinstance(ip_adds, str): ip_adds = [ip_adds]
    if isinstance(descrs, str): descrs = [descrs]

    dest_ports = generate_dest_ports(len(ip_adds)*len(protocols))
    counter = 0
    token = pfsense.get_token()
    for protocol, local_port in zip(protocols, local_ports):
        for ip_add, descr in zip(ip_adds, descrs):
            dest_port = dest_ports[counter % len(dest_ports)]
            protocol = protocol.lower()
            dest_port = str(dest_port)
            print("----------------------")
            print(f"protocol={protocol}")
            print(pfsense.add_port_forward_rule(protocol, dest_port, ip_add, local_port, descr, token))
            print(pfsense.add_firewall_rule(protocol, dest_port, ip_add, descr, token))
            port_rule = get_object_or_404(PortRules, request_id=request_id, dest_ports=local_port)
            DestinationPorts.objects.create(port_rule=port_rule, dest_port=dest_port)
            counter+=1
    time.sleep(3)
    pfsense.apply_changes(token)

    return dest_ports

def update_port_forward_rule(vm_name, ip_add):
    token = pfsense.get_token()
    pfsense.edit_firewall_rule(get_firewall_rule(vm_name, token), ip_add, token)
    pfsense.edit_port_forward_rule(get_port_forward_rule(vm_name, token), ip_add, token)
    time.sleep(3)
    pfsense.apply_changes(token)

def delete_port_forward_rules(vm_names):
    token = pfsense.get_token()
    for vm_name in vm_names:
        pfsense.delete_firewall_rule(get_firewall_rule(vm_name, token), token)
        pfsense.delete_port_forward_rule(get_port_forward_rule(vm_name, token), token)
        time.sleep(3)