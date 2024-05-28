from django.contrib import admin

# Register your models here.
from .models import RequestEntry
from .models import Comment
from .models import UserProfile

admin.site.register(RequestEntry)
admin.site.register(Comment)
admin.site.register(UserProfile)