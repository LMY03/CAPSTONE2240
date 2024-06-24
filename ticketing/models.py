from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta
import json

def expiration_date_default():
    return date.today() + timedelta(days=90)

def date_needed_default():
    return date.today() + timedelta(days=3)

class VMTemplates (models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length= 90)
    storage = models.IntegerField(default= 1)

class RequestEntry(models.Model):
    expirationDateDefault = expiration_date_default
    dateNeededDefault = date_needed_default
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', "PENDING"
        FOR_REVISION = 'FOR_REVISION', "FOR REVISION"
        PROCESSING = 'PROCESSING', "PROCESSING"
        ONGOING = 'ONGOING', "ONGOING"  # Tentative
        COMPLETED = 'COMPLETED', "COMPLETED"
        REJECTED = 'REJECTED', "REJECTED"
        DELETED = 'DELETED', "DELETED"


    status = models.CharField(
        max_length=20, 
        choices=Status.choices,
        default=Status.PENDING)

    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_entries')
    fulfilled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fulfilled_entries')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_entries')
    template = models.ForeignKey(VMTemplates, on_delete=models.SET_NULL, null=True)
    cores = models.IntegerField(default=1)
    # security options
    date_needed = models.DateField(default = dateNeededDefault)
    expiration_date = models.DateField(default = expirationDateDefault)
    isExpired = models.BooleanField(default=False)
    requestDate = models.DateTimeField (default = timezone.now)
    ram = models.IntegerField(default=2)
    #storage = models.FloatField(default= 0)
    has_internet = models.BooleanField(default=False)
    other_config = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return f"{self.id} - {self.status}"


class RequestEntryAudit(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', "PENDING"
        FOR_REVISION = 'FOR_REVISION', "FOR REVISION"
        PROCESSING = 'PROCESSING', "PROCESSING"
        ONGOING = 'ONGOING', "ONGOING"  # Tentative
        COMPLETED = 'COMPLETED', "COMPLETED"
        REJECTED = 'REJECTED', "REJECTED"
        DELETED = 'DELETED', "DELETED"

    request_entry = models.ForeignKey('RequestEntry', on_delete=models.CASCADE, related_name='audits')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_date = models.DateTimeField(auto_now_add=True)
    changes = models.TextField()  # Storing JSON as a string

    def __str__(self):
        return f"Audit for RequestEntry {self.request_entry.id} by {self.changed_by}"

    def set_changes(self, changes_dict):
        self.changes = json.dumps(changes_dict)
        self.save()

    def get_changes(self):
        return json.loads(self.changes)

class RequestUseCase (models.Model):
    request = models.ForeignKey(RequestEntry, on_delete= models.CASCADE)
    request_use_case = models.CharField(max_length=45, null = True , default = 'CLASS_COURSE')
    vm_count = models.IntegerField(default=1, null = True)

# class GroupList (models.Model):
#     user = models.CharField(null=False, max_length=50, default=" ")
#     request_use_case = models.ForeignKey(RequestUseCase, on_delete=models.CASCADE)
#     group_number = models.IntegerField(default=1)


class PortRules (models.Model):
    request = models.ForeignKey(RequestEntry, on_delete= models.CASCADE)
    protocol = models.CharField (max_length=45, blank= True, null = True)
    dest_ports = models.CharField (max_length=45, blank= True, null = True)
    description = models.TextField(blank= True, null = True)

class UserProfile (models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField (max_length= 20, choices=USER_TYPE_CHOICES, default='student')
    #request_use_case = models.ForeignKey(RequestUseCase, on_delete= models.CASCADE, null = True)

    def __str__(self) -> str:
        return f"{self.user.username} - Role: {self.user_type}"

class Comment(models.Model):
    request_entry = models.ForeignKey(RequestEntry, on_delete=models.CASCADE)
    comment = models.TextField()
    date_time = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('id', 'request_entry')

    def __str__(self):
        return f"Comment {self.id} on {self.request_entry_id}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()