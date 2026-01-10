from django import forms
from .models import Attendee

class AttendeeForm(models.Model):
    class Meta:
        model = Attendee
        fields = ['email', 'first_name', 'last_name', 'address', 'city', 'state', 'zip_code', 'phone', 'heard_from']
