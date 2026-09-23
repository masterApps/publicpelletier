from django import forms
from django.core.exceptions import ValidationError

from .models import Meetings

class MeetingsForm(forms.ModelForm):
    class Meta:
        model = Meetings
        fields = ('location', 'address', 'host', 'phone', 'date_start', 'date_end')
        