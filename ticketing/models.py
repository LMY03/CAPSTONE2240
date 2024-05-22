from django.db import models
from django.utils.translation import gettext_lazy as _

class OSList (models.Model):
    os_code = models.CharField(max_length=45)
    os_name = models.CharField(max_length=90)

    def __str__(self):
        return self.os_code

    class Meta:
        db_table = 'os_list'

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
    template_id = models.ForeignKey(OSList, on_delete=models.CASCADE)
    cores = models.IntegerField(default=1)
    ram = models.IntegerField(default=2)
    storage = models.FloatField(default=2.0)
    has_internet = models.BooleanField(default=False)
    use_case = models.CharField(max_length=255, blank=True, null=True)  # New field
    other_config = models.TextField(blank=True, null=True)  # New field
    vm_count = models.IntegerField(default = 1)
    assigned_to = models.CharField (max_length=45,null = True)
    revision_comments = models.TextField(null = True)