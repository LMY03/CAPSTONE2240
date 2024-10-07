from django.db import models
# from django.contrib.auth.models import User

from users.models import User
# from proxmox.models import VirtualMachines

# Create your models here.
class GuacamoleUser(models.Model):
    system_user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    username = models.CharField(max_length=150)
    password = models.CharField(max_length=128)

class GuacamoleConnection(models.Model):
    user = models.ForeignKey(GuacamoleUser, on_delete=models.DO_NOTHING)
    vm = models.OneToOneField('proxmox.VirtualMachines', on_delete=models.DO_NOTHING)
    connection_id = models.IntegerField()
    connection_group_id = models.IntegerField()

    class Protocol(models.TextChoices):
        RDP = 'rdp'
        VNC = 'vnc'
        SSH = 'ssh'

    def is_ssh(protocol) : return GuacamoleConnection.Protocol.SSH == protocol
    def is_rdp(protocol) : return GuacamoleConnection.Protocol.RDP == protocol
    def is_vnc(protocol) : return GuacamoleConnection.Protocol.VNC == protocol
