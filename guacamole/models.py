from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# class GuacamoleUser(models.Model):
#     system_user = models.ForeignKey(User)
#     username = models.CharField(max_length=45)
#     password = models.CharField(max_length=45)

class GuacamoleConnection(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    connection_id = models.IntegerField()