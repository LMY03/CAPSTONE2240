from django.shortcuts import get_object_or_404
from django.db.models.signals import post_save
from django.dispatch import receiver

from guacamole import guacamole

from .models import User
from guacamole.models import GuacamoleUser
from proxmox.models import VirtualMachines

@receiver(post_save, sender=User)
def create_guacamole_user(sender, instance : User, created, **kwargs):
    # Trigger for create Guacamole User Account After User Creation
    if created:
        # If a new user is created in Django, trigger the Guacamole user creation
        username = instance.username
        
        guacamole_password = User.objects.make_random_password()
        guacamole.create_user(username, guacamole_password)

        GuacamoleUser.objects.create(
            system_user=instance, 
            username=username,
            password=guacamole_password,
        )
        
    # Trigger for create Guacamole User Account after USER is deactivated (is_active set to False)
    elif not instance.is_active:
        guacamole.delete_user(instance.username)

        if instance.is_student() and "_" not in instance.username:
            print("=====================")
            print("_" not in instance.username)
            print(f"system username: {instance.username}")
            request_id = get_object_or_404(VirtualMachines, vm_name=instance.username).request.pk
            instance.username = f"{instance.username}_{request_id}"
            instance.save()
