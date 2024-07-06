from django.db import models
from django.shortcuts import get_object_or_404
from decouple import config

class Nodes(models.Model):
    name = models.CharField(max_length=45)

class VirtualMachines(models.Model):
    vm_id = models.IntegerField()
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.DecimalField(max_digits=5, decimal_places=2)
    ip_add = models.CharField(max_length=15)
    request = models.ForeignKey('ticketing.RequestEntry', on_delete=models.CASCADE)
    node = models.CharField(max_length=45)
    is_lxc = models.BooleanField(default=False)
    # vm_password = models.CharField(max_length=45)

    class Status(models.TextChoices): 
        ACTIVE = 'ACTIVE'
        SHUTDOWN = 'SHUTDOWN'
        DESTROYED = 'DESTROYED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    def get_vm_userpass(self):
        vm_user = VMUser.objects.get(vm=self)
        try:
            vm_user = VMUser.objects.get(vm=self)
            return {'vm_user': vm_user.username, 'vm_pass': vm_user.password}
        except VMUser.DoesNotExist:
            return {'vm_user': config('DEFAULT_VM_USERNAME'), 'vm_pass': config('DEFAULT_VM_PASSWORD')}

class VMUser(models.Model):
    vm = models.ForeignKey(VirtualMachines, on_delete=models.CASCADE)
    username = models.CharField(max_length=45)
    password = models.CharField(max_length=45)