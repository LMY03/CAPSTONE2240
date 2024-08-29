from django.db import models
from decouple import config

class Nodes(models.Model):
    name = models.CharField(max_length=45)

class VirtualMachines(models.Model):
    vm_id = models.IntegerField()
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.DecimalField(max_digits=5, decimal_places=2)
    ip_add = models.CharField(max_length=15, null=True, default=None)
    request = models.ForeignKey('ticketing.RequestEntry', on_delete=models.DO_NOTHING)
    node = models.ForeignKey(Nodes, on_delete=models.DO_NOTHING)
    is_lxc = models.BooleanField(default=False)
    system_password = models.CharField(max_length=45, null=True, default=None)
    # vm_password = models.CharField(max_length=45, default=config('DEFAULT_VM_PASSWORD'))

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