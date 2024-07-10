from django.shortcuts import get_list_or_404
# import redis, os

from . import pfsense

from ticketing.models import RequestEntry, PortRules

# redis_host = os.getenv('REDIS_HOST', 'redis')
# redis_client = redis.StrictRedis(host=redis_host, port=6379, db=0)

# Create your views here.

def get_port_forward_rule(vm_name):
    rules = pfsense.get_port_forward_rules()
    for rule in rules:
        if rule['descr'] == vm_name: return rule['id']

def get_firewall_rule(vm_name):
    rules = pfsense.get_port_forward_rules()
    for rule in rules:
        if rule['descr'] == vm_name: return rule['id']

def generate_dest_ports():
    port_rules = []
    request_entries = RequestEntry.objects.filter(status=RequestEntry.Status.ONGOING) # maybe also add completed
    for request_entry in request_entries:
        for port_rule in PortRules.objects.filter(request_id=request_entry.id):
            port_rules.append(port_rule)

    return

def add_port_forward_rules(protocols, ip_adds, local_ports, descrs):
    dest_ports = generate_dest_ports()
    # lock = redis_client.lock('pfsense_lock', timeout=60)
    # with lock:
    #     for protocol, destination_port, ip_add, local_port, descr in protocols, dest_ports, ip_adds, local_ports, descrs:
    #         pfsense.add_firewall_rule(protocol, destination_port, ip_add, descr)
    #         pfsense.add_port_forward_rule(protocol, destination_port, ip_add, local_port, descr)
    # pfsense.apply_changes()

def update_port_forward_rule_ip_adds(vm_names, ip_adds):
    return
    # lock = redis_client.lock('pfsense_lock', timeout=60)
    # with lock:
    #     for vm_name, ip_add in vm_names, ip_adds:
    #         port_forward_id = get_port_forward_rule(vm_name)
    #         firewall_id = get_firewall_rule(vm_name)
    #         pfsense.edit_port_forward_rule(port_forward_id, ip_add)
    #         pfsense.edit_firewall_rule(firewall_id, ip_add)

def delete_port_forward_rules(vm_names):
    return
    # lock = redis_client.lock('pfsense_lock', timeout=60)
    # with lock:
    #     for vm_name in vm_names:
    #         port_forward_id = get_port_forward_rule(vm_name)
    #         firewall_id = get_firewall_rule(vm_name)
    #         pfsense.delete_port_forward_rule(port_forward_id)
    #         pfsense.delete_firewall_rule(firewall_id)