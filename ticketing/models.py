from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import json

from guacamole.models import GuacamoleConnection

def expiration_date_default():
    return date.today() + timedelta(days=90)

def date_needed_default():
    return date.today() + timedelta(days=3)

class VMTemplates(models.Model):
    vm_id = models.CharField(max_length=45)
    vm_name = models.CharField(max_length=90)
    cores = models.IntegerField()
    ram = models.IntegerField()
    storage = models.IntegerField()
    node = models.CharField(max_length=45)
    is_lxc = models.BooleanField(default=False)
    
    guacamole_protocol = models.CharField(
        max_length=10,
        choices=GuacamoleConnection.Protocol.choices
    )

class RequestEntry(models.Model):

    ram = models.IntegerField(default=2)
    #storage = models.FloatField(default= 0)
    has_internet = models.BooleanField(default=False)
    other_config = models.TextField(blank=True, null=True)
    
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        FOR_REVISION = 'FOR REVISION'
        PROCESSING = 'PROCESSING'
        ACCEPTED = 'ACCEPTED'
        ONGOING = 'ONGOING'
        COMPLETED = 'COMPLETED'
        DELETED = 'DELETED'
        REJECTED = 'REJECTED'

    status = models.CharField(
        max_length=20, 
        choices=Status.choices,
        default=Status.PENDING)

    requester = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='requested_entries')
    fulfilled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fulfilled_entries')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_entries')
    template = models.ForeignKey(VMTemplates, on_delete=models.DO_NOTHING)
    cores = models.IntegerField(default=1)
    # security options
    isExpired = models.BooleanField(default=False)
    requestDate = models.DateTimeField(default=timezone.localtime)

    date_needed = models.DateField(default=expiration_date_default)
    expiration_date = models.DateField(null=True)

    is_vm_tested = models.BooleanField(default=False)

    def is_recurring(self) : return self.expiration_date == None

    def get_requester(self):
        requester = self.requester
        if requester.first_name != None and requester.last_name != None : return f'{requester.first_name} {requester.last_name}'
        else : return requester.username

    def get_assigned_to(self):
        assigned_to = self.assigned_to
        if assigned_to.first_name != None and assigned_to.last_name != None : return f'{assigned_to.first_name} {assigned_to.last_name}'
        else : return assigned_to.username

    def get_fulfilled_by(self):
        fulfilled_by = self.fulfilled_by
        if fulfilled_by.first_name != None and fulfilled_by.last_name != None : return f'{fulfilled_by.first_name} {fulfilled_by.last_name}'
        else : return fulfilled_by.username

    def is_pending(self) : return self.status == RequestEntry.Status.PENDING
    def is_for_revision(self) : return self.status == RequestEntry.Status.FOR_REVISION
    def is_processing(self) : return self.status == RequestEntry.Status.PROCESSING
    def is_ongoing(self) : return self.status == RequestEntry.Status.ONGOING
    def is_completed(self) : return self.status == RequestEntry.Status.COMPLETED
    def is_accepted(self) : return self.status == RequestEntry.Status.ACCEPTED
    def is_deleted(self) : return self.status == RequestEntry.Status.DELETED
    def is_rejected(self) : return self.status == RequestEntry.Status.REJECTED

    def get_request_type(self):
        request_use_case = RequestUseCase.objects.filter(request=self)[0].request_use_case
        if request_use_case == 'RESEARCH' : return 'Research'
        elif request_use_case == 'THESIS' : return 'Thesis'
        elif request_use_case == 'TEST' : return 'Test'
        else : return 'Class Course'

    def is_course(self) : return self.get_request_type() == 'Class Course'
    def is_research(self) : return self.get_request_type() == 'Research'
    def is_thesis(self) : return self.get_request_type() == 'Thesis'
    def is_test(self) : return self.get_request_type() == 'Test'

    def get_total_no_of_vm(self):
        request_use_cases = RequestUseCase.objects.filter(request=self).values('request_use_case', 'vm_count')
        total_no_of_vm = 0
        for request_use_case in request_use_cases : total_no_of_vm += int(request_use_case['vm_count'])
        return total_no_of_vm

    def __str__(self):
        return f"{self.id} - {self.status}"

class RequestEntryAudit(models.Model):
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

class RequestUseCase(models.Model):
    request = models.ForeignKey(RequestEntry, on_delete= models.CASCADE)
    request_use_case = models.CharField(max_length=45, null=True, default='CLASS_COURSE')
    vm_count = models.IntegerField(default=1, null=True)

# class GroupList (models.Model):
#     user = models.CharField(null=False, max_length=50, default=" ")
#     request_use_case = models.ForeignKey(RequestUseCase, on_delete=models.CASCADE)
#     group_number = models.IntegerField(default=1)


class PortRules(models.Model):
    request = models.ForeignKey(RequestEntry, on_delete= models.CASCADE)
    protocol = models.CharField (max_length=45)
    dest_ports = models.CharField (max_length=45)
    #description = models.TextField(blank= True, null = True)

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
    date_time = models.DateTimeField(default=timezone.localtime)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('id', 'request_entry')

    def __str__(self):
        return f"Comment {self.id} on {self.request_entry_id}"

# @reciever(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     # print("------------------------------")
#     if created:
#         UserProfile.objects.create(user=instance)
#         # guacamole_username = instance.username
#         # guacamole_password = instance.password
#         # GuacamoleUser(user=instance, username=guacamole_username, password=guacamole_password)
#         # guacamole.create_user(guacamole_username, guacamole_password)
        
#         # print("created system user")
#         # create_guacamole_user(instance)
#     else:
#         instance.userprofile.save()

# @receiver(post_save, sender=User)
# def create_or_update_user_profile(sender, instance, created, **kwargs):
#     print("------------------------------")
#     if created:
#         print("created system user")
#     # else:


class IssueTicket(models.Model):
    subject = models.CharField(max_length=100)
    description = models.CharField(max_length=10000)
    date_created = models.DateTimeField(default=timezone.localtime)
    resolve_date = models.DateTimeField(null=True)
    request = models.ForeignKey(RequestEntry, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def is_resolved(self) : return self.resolve_date != None

    def get_status(self):
        if self.is_resolved() : return "Resolved"
        else : return "Unresolved"

    def get_requester(self):
        requester = self.created_by
        if requester.first_name != None and requester.last_name != None : return f'{requester.first_name} {requester.last_name}'
        else : return requester.username

    def resolve_ticket(self):
        self.resolve_date = timezone.localtime()
        self.save()

class IssueFile(models.Model):
    file = models.FileField(upload_to='issue_files/')
    uploaded_date = models.DateTimeField(default=timezone.localtime)

    ticket = models.ForeignKey(IssueTicket, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

class IssueComment(models.Model):
    ticket = models.ForeignKey(IssueTicket, on_delete=models.CASCADE)
    comment = models.TextField()
    date_time = models.DateTimeField(default=timezone.localtime)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class IssueCommentFile(models.Model):
    file = models.FileField(upload_to='issue_files/comments/')
    uploaded_date = models.DateTimeField(default=timezone.localtime)

    comment = models.ForeignKey(IssueComment, on_delete=models.CASCADE)