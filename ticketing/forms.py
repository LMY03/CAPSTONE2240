from django import forms
from django.contrib.auth.models import User

class UserAdminForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_active', 'is_staff', 'is_superuser')