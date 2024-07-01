from django.db import models
from django.contrib.auth.models import User

from proxmox.models import VirtualMachines

# Create your models here.
class GuacamoleUser(models.Model):
    system_user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        DELETED = 'DELETED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

class GuacamoleConnection(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.DO_NOTHING)
    vm = models.OneToOneField(VirtualMachines, on_delete=models.DO_NOTHING)
    connection_id = models.IntegerField()
    connection_group_id = models.IntegerField()

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE'
        DELETED = 'DELETED'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )