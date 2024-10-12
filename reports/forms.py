from django import forms

from ticketing.models import RequestEntry, RequestUseCase

class TicketingReportForm(forms.Form):
    
    start_date = forms.DateTimeField(
        label='Start Date',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        }),
        required=True,
    )
    
    end_date = forms.DateTimeField(
        label='End Date',
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        }),
        required=True,
    )

    use_case = forms.MultipleChoiceField(
        label='Use Case',
        choices=RequestUseCase.UseCase.choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
    )

    class_course_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search for a course',}),  # Hidden initially
        label='Class Course Search'
    )

