from django.db import models
from django.contrib.auth.models import User
from proxmox.models import VirtualMachines
# Create your models here.
# class GuacamoleUser(models.Model):
#     system_user = models.ForeignKey(User)
#     username = models.CharField(max_length=45)
#     password = models.CharField(max_length=45)

class GuacamoleConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    vm = models.OneToOneField(VirtualMachines, on_delete=models.CASCADE, default=1)
    connection_id = models.IntegerField()

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        DELETED = 'DELETED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )