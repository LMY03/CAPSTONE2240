from django.db import models

from ticketing.models import PortRules

# Create your models here.

class DestinationPorts(models.Model):
    port_rule = models.ForeignKey(PortRules, on_delete=models.CASCADE)
    dest_port = models.IntegerField()