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
    vm_password = models.CharField(max_length=45, default=config('DEFAULT_VM_PASSWORD'))

    class Status(models.TextChoices): 
        ACTIVE = 'ACTIVE'
        SHUTDOWN = 'SHUTDOWN'
        DESTROYED = 'DESTROYED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )