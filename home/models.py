# home/models.py
from django.db import models
from django.http import HttpResponse
import mimetypes


class SlideModel(models.Model):
    title = models.CharField(max_length=50, default="none")
    file_data = models.BinaryField()
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save_file(self, uploaded_file):
        """Save an uploaded file to the binary field"""
        self.file_data = uploaded_file.read()
        self.file_name = uploaded_file.name
        self.file_size = uploaded_file.size
        self.content_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0]

    def get_file_response(self):
        """Return an HttpResponse with the file data"""
        response = HttpResponse(self.file_data, content_type=self.content_type)
        response['Content-Disposition'] = f'inline; filename="{self.file_name}"'
        return response

    def __str__(self):
        return f"{self.title} - {self.file_name}"
