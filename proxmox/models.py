from django.db import models

from django.shortcuts import get_object_or_404

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

    class Status(models.TextChoices): 
        ACTIVE = 'ACTIVE'
        SHUTDOWN = 'SHUTDOWN'
        DESTROYED = 'DESTROYED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    def change_vm_user(self, username, password):
        vm_user = get_object_or_404(VMUser, vm=self)
        vm_user.username = username
        vm_user.password = password
        vm_user.save()

class VMUser(models.Model):
    vm = models.ForeignKey(VirtualMachines, on_delete=models.CASCADE)
    username = models.CharField(max_length=45)
    password = models.CharField(max_length=45)