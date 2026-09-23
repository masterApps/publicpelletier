from django.contrib import admin
from django import forms
from .models import Materials


class MaterialsForm(forms.ModelForm):
    pdf_upload = forms.FileField(required=False, help_text="Upload PDF file")

    class Meta:
        model = Materials
        fields = ['title', 'body']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('pdf_upload'):
            instance.save_pdf(self.cleaned_data['pdf_upload'])
        if commit:
            instance.save()
        return instance


class MaterialAdmin(admin.ModelAdmin):
    form = MaterialsForm
    list_display = ['title', 'pdf_name', 'pdf_size', 'publish_date']
    readonly_fields = ['pdf_name', 'pdf_size', 'content_type', 'uploaded_at']


admin.site.register(Materials, MaterialAdmin)