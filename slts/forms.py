from django import forms
from .models import Attendee

class AttendeeForm(forms.ModelForm):
    class Meta:
        model = Attendee
        fields = ['first_name', 'last_name', 'address', 'city', 'state', 'zip_code', 'email', 'phone', 'heard_from']
