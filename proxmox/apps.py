from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ProxmoxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'proxmox'

    def ready(self):

        from .models import Nodes, VMTemplates
        from guacamole.models import GuacamoleConnection

        def create_initial_nodes(sender, **kwargs):
            if not Nodes.objects.exists():
                Nodes.objects.create(
                    name='pve',
                )
                Nodes.objects.create(
                    name='jin',
                )

        def create_initial_vm_templates(sender, **kwargs):
            if not VMTemplates.objects.exists():
                VMTemplates.objects.create(
                    vm_id=3000,
                    vm_name='Ubuntu-Desktop-24 (GUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.RDP,
                    is_lxc=False,
                    is_active=True,
                    node=1
                )
                VMTemplates.objects.create(
                    vm_id=3001,
                    vm_name='Ubuntu-Desktop-22 (GUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.RDP,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=3000,
                    vm_name='Ubuntu-Server-24 (TUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=3001,
                    vm_name='Ubuntu-Server-22 (TUI)',
                    cores=1,
                    ram=1024,
                    storage=15,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=False,
                    is_active=True,
                    node=1,
                )
                VMTemplates.objects.create(
                    vm_id=4000,
                    vm_name='Ubuntu-LXC-23',
                    cores=1,
                    ram=1024,
                    storage=10,
                    guacamole_protocol=GuacamoleConnection.Protocol.SSH,
                    is_lxc=True,
                    is_active=True,
                    node=1,
                )

        post_migrate.connect(create_initial_nodes)
        post_migrate.connect(create_initial_vm_templates)
