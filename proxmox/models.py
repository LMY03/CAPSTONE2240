from django.db import models

from guacamole.models import GuacamoleConnection

class Nodes(models.Model):
    name = models.CharField(max_length=45)

class VMTemplates(models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.IntegerField()
    node = models.CharField(max_length=45)
    is_lxc = models.BooleanField(default=False)
    
    guacamole_protocol = models.CharField(
        max_length=10,
        choices=GuacamoleConnection.Protocol.choices
    )

class VirtualMachines(models.Model):
    vm_id = models.IntegerField()
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.DecimalField(max_digits=5, decimal_places=2)
    ip_add = models.CharField(max_length=15, null=True, default=None)
    request = models.ForeignKey('ticketing.RequestEntry', on_delete=models.DO_NOTHING)
    node = models.ForeignKey(Nodes, on_delete=models.DO_NOTHING)

    class Status(models.TextChoices): 
        CREATING = 'CREATING'
        ACTIVE = 'ACTIVE'
        SHUTDOWN = 'SHUTDOWN'
        DESTROYED = 'DESTROYED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATING
    )

    def is_lxc(self) : return self.request.is_lxc() 

    def machine_type(self):
        if self.is_lxc() : return "Linux Container"
        else: return "Virtual Machine"

    def set_ip_add(self, ip_add):
        self.ip_add = ip_add
        self.save()

    def is_active(self) : return self.status == VirtualMachines.Status.ACTIVE
    def is_shutdown(self) : return self.status == VirtualMachines.Status.SHUTDOWN
    def is_destroyed(self) : return self.status == VirtualMachines.Status.DESTROYED

    def set_active(self):
        self.status = VirtualMachines.Status.ACTIVE
        self.save()

    def set_shutdown(self):
        self.status = VirtualMachines.Status.SHUTDOWN
        self.save()

    def set_destroyed(self):
        self.status = VirtualMachines.Status.DESTROYED
        self.save()
    
