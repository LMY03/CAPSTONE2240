from django.db import models
from django.apps import apps

# Remove the direct import
from ticketing.models import RequestEntry

class VirtualMachines(models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.DecimalField(max_digits=5, decimal_places=2)
    ip_add = models.CharField(max_length=15, null=True)
    request = models.ForeignKey(RequestEntry, on_delete=models.CASCADE, null=True)

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        SHUTDOWN = 'SHUTDOWN'
        DESTROYED = 'DESTROYED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

class VMUser(models.Model):
    vm = models.ForeignKey(VirtualMachines, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=45)
    password = models.CharField(max_length=45)
