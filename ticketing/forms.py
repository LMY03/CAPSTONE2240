from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import VMTemplates, IssueTicket, IssueComment

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_active', 'is_staff', 'is_superuser')

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password:
            return self.initial["password"]
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user

class AddVMTemplates(forms.ModelForm):

    class Meta:
        model = VMTemplates
        fields = ('vm_id', 'vm_name', 'node', 'storage', 'is_lxc', 'guacamole_protocol')

    def save(self, commit=True):
        vmtemplate = super().save(commit=False)
        # This is where the API call starts
        # Where it ends

        # Setting of the core ram and storage
        vmtemplate.cores = 1
        vmtemplate.ram = 2048
        if commit:
            vmtemplate.save()
        return vmtemplate
    
class IssueTicketForm(forms.ModelForm):
    class Meta:
        model = IssueTicket
        fields = ['subject', 'category', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }
    
    request_entry = forms.CharField(widget=forms.HiddenInput())

class IssueCommentForm(forms.ModelForm):
    class Meta:
        model = IssueComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    ticket = forms.CharField(widget=forms.HiddenInput())