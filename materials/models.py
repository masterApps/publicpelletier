# materials/models.py
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.http import HttpResponse
import mimetypes


class Materials(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    body = models.TextField()
    publish_date = models.DateField(auto_now_add=True)

    # Replace FileField with binary storage
    pdf_data = models.BinaryField()
    pdf_name = models.CharField(max_length=255)
    pdf_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100, default='application/pdf')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save_pdf(self, uploaded_file):
        """Save an uploaded PDF file to the binary field"""
        self.pdf_data = uploaded_file.read()
        self.pdf_name = uploaded_file.name
        self.pdf_size = uploaded_file.size
        self.content_type = uploaded_file.content_type or 'application/pdf'

    def get_pdf_response(self):
        """Return an HttpResponse with the PDF data"""
        response = HttpResponse(self.pdf_data, content_type=self.content_type)
        response['Content-Disposition'] = f'attachment; filename="{self.pdf_name}"'
        return response

    def get_absolute_url(self):
        return reverse('article_details', args=[str(self.slug)])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_pdf_filename(self):
        return self.pdf_name
