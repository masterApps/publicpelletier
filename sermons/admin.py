from django.contrib import admin
from django import forms
from .models import AudioSermon, AudioUploadSession


class AudioSermonForm(forms.ModelForm):
    audio_upload = forms.FileField(required=False, help_text="Upload audio file")

    class Meta:
        model = AudioSermon
        fields = ['date', 'title', 'passage']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('audio_upload'):
            instance.save_audio(self.cleaned_data['audio_upload'])
        if commit:
            instance.save()
        return instance


class SermonAdmin(admin.ModelAdmin):
    form = AudioSermonForm
    list_display = ['title', 'passage', 'date', 'audio_name', 'audio_size']
    readonly_fields = ['audio_name', 'audio_size', 'content_type', 'uploaded_at']

class AudioUploadSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'audio_name', 'content_type', 'created_at', 'completed_at', 'is_complete',
                    'total_size', 'uploaded_size', 'total_chunks_expected', 'chunks_received']


admin.site.register(AudioSermon, SermonAdmin)
admin.site.register(AudioUploadSession, AudioUploadSessionAdmin)