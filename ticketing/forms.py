from django import forms
# from django.contrib.auth.models import User
from proxmox.models import VMTemplates
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import IssueTicket, IssueComment

# class UserCreationForm(forms.ModelForm):
#     password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
#     password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

#     class Meta:
#         model = User
#         fields = ('username', 'email')

#     def clean_password2(self):
#         password1 = self.cleaned_data.get("password1")
#         password2 = self.cleaned_data.get("password2")
#         if password1 and password2 and password1 != password2:
#             raise forms.ValidationError("Passwords don't match")
#         return password2

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.set_password(self.cleaned_data["password1"])
#         if commit:
#             user.save()
#         return user

# class UserChangeForm(forms.ModelForm):
#     password = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)

#     class Meta:
#         model = User
#         fields = ('username', 'email', 'password', 'is_active', 'is_staff', 'is_superuser')

#     def clean_password(self):
#         password = self.cleaned_data.get("password")
#         if not password:
#             return self.initial["password"]
#         return password

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         password = self.cleaned_data.get("password")
#         if password:
#             user.set_password(password)
#         if commit:
#             user.save()
#         return user

class AddVMTemplates(forms.ModelForm):

    class Meta:
        model = VMTemplates
        fields = ('vm_id','guacamole_protocol')
        widgets = {
            'vm_id': forms.TextInput(attrs={'class': 'form-control'}),
            'guacamole_protocol': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        vmtemplate = super().save(commit=False)
        
        vmtemplate.vm_id = self.cleaned_data['vm_id']
        vmtemplate.guacamole_protocol = self.cleaned_data['guacamole_protocol']
        # This is where the API call starts
        vmtemplate.cores = 1
        vmtemplate.ram = 2048
        vmtemplate.node = 'Mayari'
        vmtemplate.vm_name = 'VMTEMPLATE NAME 30gb'
        vmtemplate.storage = '30'
        # Where it ends
        if commit:
            vmtemplate.save()
        return vmtemplate
    

class EditVMTemplates(forms.ModelForm):

    class Meta:
        model = VMTemplates
        fields = ('vm_name', 'guacamole_protocol')
        widgets = {
            'vm_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guacamole_protocol': forms.Select(attrs={'class': 'form-control'}),
        }


    def save(self, commit=True):
        vmtemplate = self.instance  # This is the existing instance
        # Update the fields based on the form data
        vmtemplate.vm_name = self.cleaned_data['vm_name']
        vmtemplate.guacamole_protocol = self.cleaned_data['guacamole_protocol']
        # This is where the API call starts
        vmtemplate.cores = 1
        vmtemplate.ram = 2048
        vmtemplate.vm_id = '3001'
        vmtemplate.node = 'Mayari'
        vmtemplate.storage = '30'
        
    
        # Where it ends
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