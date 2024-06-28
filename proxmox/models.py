from django.db import models

class VirtualMachines(models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.DecimalField(max_digits=5, decimal_places=2)
    ip_add = models.CharField(max_length=15)
    request = models.ForeignKey('ticketing.RequestEntry', on_delete=models.CASCADE)
    node = models.CharField(max_length=45)

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
    vm = models.ForeignKey(VirtualMachines, on_delete=models.CASCADE)
    username = models.CharField(max_length=45)
    password = models.CharField(max_length=45)
