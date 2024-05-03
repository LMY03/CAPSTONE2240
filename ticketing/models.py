from django.db import models

# Create your models here.
class RequestEntry(models.Model):
    #  TODO: add if needed
    requester_id = models.CharField(max_length=30)
    template_id = models.CharField(max_length=30)
    cores = models.IntegerField(default=1)
    ram = models.IntegerField(default=2)
    storage = models.FloatField(default=2.0)
    has_internet = models.BooleanField(default=False)