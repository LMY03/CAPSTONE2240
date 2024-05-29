from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class OSList (models.Model):
    os_code = models.CharField(max_length=45)
    os_name = models.CharField(max_length=90)

    def __str__(self):
        return self.os_code

    class Meta:
        db_table = 'os_list'

class RequestEntry(models.Model):
    class Status(models.TextChoices):
        PENDING = "P", "PENDING"
        FOR_REVISION = 'FR', "FOR REVISION"
        CREATING = "CR", "CREATING"
        COMPLETED = "CO", "COMPLETED"
        DELETED = "D", "DELETED"

    status = models.CharField(
        max_length=10, 
        choices=Status.choices,
        default=Status.PENDING)

    requester = models.ForeignKey(User, on_delete=models.CASCADE, null= True)
    template = models.ForeignKey(OSList, on_delete=models.CASCADE, null= True)
    cores = models.IntegerField(default=1)
    ram = models.IntegerField(default=2)
    storage = models.FloatField(default=2.0)
    has_internet = models.BooleanField(default=False)
    use_case = models.CharField(max_length=255, blank=True, null=True)
    other_config = models.TextField(blank=True, null=True)
    vm_count = models.IntegerField(default=1)
    assigned_to = models.CharField(max_length=45, null=True)

    def __str__(self):
        return f"{self.id} - {self.status}"

class UserProfile (models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('tsg', 'TSG'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField (max_length= 20, choices=USER_TYPE_CHOICES, default='student')

    def __str__(self) -> str:
        return self.user.username

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