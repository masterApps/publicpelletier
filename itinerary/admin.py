from django.contrib import admin
from .models import Meetings


class MeetingAdmin(admin.ModelAdmin):
    list_display = ['location', 'city', 'date_start']

admin.site.register(Meetings, MeetingAdmin)
