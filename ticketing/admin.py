from django.contrib import admin
from .models import RequestEntry, UserProfile, VMTemplates
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .forms import UserCreationForm, UserChangeForm, AddVMTemplates

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

class CustomUserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username','email', 'password1', 'password2'),
        }),
    )

    inlines = (UserProfileInline,)

class CustomVMTemplateAdmin(admin.ModelAdmin):
    form = AddVMTemplates

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(VMTemplates, CustomVMTemplateAdmin)
# admin.site.register(UserProfile)
# admin.site.register(RequestEntry)
