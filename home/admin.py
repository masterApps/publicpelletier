from django.contrib import admin
from django import forms
from .models import SlideModel


class SlideModelForm(forms.ModelForm):
    file_upload = forms.FileField(required=False, help_text="Upload image file")

    class Meta:
        model = SlideModel
        fields = ['title']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('file_upload'):
            instance.save_file(self.cleaned_data['file_upload'])
        if commit:
            instance.save()
        return instance


class CarouselAdmin(admin.ModelAdmin):
    form = SlideModelForm
    list_display = ['title', 'file_name', 'file_size', 'uploaded_at']
    readonly_fields = ['file_name', 'file_size', 'content_type', 'uploaded_at']


admin.site.register(SlideModel, CarouselAdmin)