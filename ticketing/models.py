from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta

# class OSList (models.Model):
#     os_code = models.CharField(max_length=45)
#     os_name = models.CharField(max_length=90)

#     def __str__(self):
#         return self.os_code

#     class Meta:
#         db_table = 'os_list'

class VMTemplates (models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length= 90)
    storage = models.IntegerField(default= 1)



class RequestEntry(models.Model):
    expirationDateDefault = date.today() + timedelta(days=90)
    dateNeededDefault = date.today() + timedelta (days = 3)
    
    class Status(models.TextChoices):
        PENDING = "P", "PENDING"
        FOR_REVISION = 'FR', "FOR REVISION"
        PROCESSING = "PRCS", "PROCESSING"
        ONGOING = "OG", "ONGOING" #Tentative
        COMPLETED = "CO", "COMPLETED"
        REJECTED = "RJ", "REJECTED"
        DELETED = "D", "DELETED"

    status = models.CharField(
        max_length=10, 
        choices=Status.choices,
        default=Status.PENDING)

    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_entries')
    fulfilledBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fulfilled_entries')
    template = models.ForeignKey(VMTemplates, on_delete=models.SET_NULL, null= True)
    cores = models.IntegerField(default=1)
    # security options
    date_needed = models.DateField(default = dateNeededDefault)
    expiration_date = models.DateField(default = expirationDateDefault)
    isExpired = models.IntegerField(default = 0)
    requestDate = models.DateTimeField (default = timezone.now)
    ram = models.IntegerField(default=2)
    storage = models.FloatField(default= 0)
    has_internet = models.BooleanField(default=False)
    use_case = models.CharField(max_length=255, blank=True, null=True)
    other_config = models.TextField(blank=True, null=True)
    vm_count = models.IntegerField(default=1)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_entries')

    def __str__(self):
        return f"{self.id} - {self.status}"

class UserProfile (models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField (max_length= 20, choices=USER_TYPE_CHOICES, default='student')

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