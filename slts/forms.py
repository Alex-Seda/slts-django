import re
from django import forms
from .models import Attendee


COMPOUND_PATTERNS = [
    r"\band\b",
    r"&",
    r",",
    r"/",
]


class AttendeeForm(forms.ModelForm):
    spouse_first_name = forms.CharField(
        required=False,
        label="Spouse First Name (optional)",
    )

    def clean_first_name(self):
        name = self.cleaned_data["first_name"].strip()

        for pattern in COMPOUND_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                raise forms.ValidationError(
                    "Please enter one person's first name only. "
                    "Use the \"Spouse first name\" field at the bottom if you are also registering your spouse."
                )

        return name

    def clean_spouse_first_name(self):
        name = self.cleaned_data.get("spouse_first_name", "").strip()
        if not name:
            return name  # empty is fine

        for pattern in COMPOUND_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                raise forms.ValidationError(
                    "Please enter one person's first name only."
                )

        return name

    class Meta:
        model = Attendee
        fields = ['first_name', 'last_name', 'address', 'city', 'state', 'zip_code', 'email', 'phone', 'heard_from']
