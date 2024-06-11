from django.contrib import admin

# Register your models here.
from .models import RequestEntry
from .models import UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .forms import UserAdminForm

class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    add_form = UserAdminForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email')
        }),
    )

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class UserAdmin(UserAdmin):
    inlines = (UserProfileInline,)



admin.site.unregister(User)

# Register the new UserAdmin
admin.site.register(User, UserAdmin)

# Register the UserProfile model (optional)
admin.site.register(UserProfile)
admin.site.register(RequestEntry)
