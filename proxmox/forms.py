from django import forms

from .models import VMTemplates

class AddVMTemplatesForm(forms.ModelForm):

    class Meta:
        model = VMTemplates
        fields = ['vm_id']
        widgets = {
            'vm_id': forms.TextInput(attrs={'class': 'form-control'}),
        }
