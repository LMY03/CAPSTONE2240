from django.db import models

# Create your models here.


# class Credentials(models.Model):
#     user_id = models.CharField(max_length=255)
#     access_token = models.CharField(max_length=255)
#     refresh_token = models.CharField(max_length=255)
#     expires_at = models.DateTimeField()  # Store when the token expires
#     created_at = models.DateTimeField(auto_now_add=True)  # When credentials were created
#     updated_at = models.DateTimeField(auto_now=True)  # When credentials were last updated

#     def __str__(self):
#         return f"{self.user.username} Credentials"
