from django.db import models

import uuid

# Create your models here.
class PortRules(models.Model):
    # request = models.ForeignKey(RequestEntry, on_delete= models.CASCADE)
    vm = models.ForeignKey('proxmox.VirtualMachines', on_delete= models.CASCADE)
    protocol = models.CharField(max_length=45)
    source_port = models.CharField(max_length=45)
    dest_port = models.CharField(max_length=45)
    rule_uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    is_disabled = models.BooleanField(default=False)

    def delete_firewall_rule(self):
        self.is_disabled = True
        self.save()
