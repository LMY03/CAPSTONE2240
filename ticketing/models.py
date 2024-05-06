from django.db import models
from django.utils.translation import gettext_lazy as _

class RequestEntry(models.Model):
    class Status(models.TextChoices):
        PENDING = "P", _("PENDING")
        FOR_REVISION = 'FR', _("FOR REVISION")
        CREATING = "CR", _("CREATING")
        COMPLETED = "CO", _("COMPLETED")
        DELETED = "D", _("DELETED")

    status = models.CharField(
        max_length=10, 
        choices=Status,
        default=Status.PENDING)

    requester_id = models.CharField(max_length=30)
    template_id = models.CharField(max_length=30)
    cores = models.IntegerField(default=1)
    ram = models.IntegerField(default=2)
    storage = models.FloatField(default=2.0)
    has_internet = models.BooleanField(default=False)