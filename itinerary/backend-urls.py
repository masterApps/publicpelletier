# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.meeting_form, name='meeting_form'),
    path('api/upload-csv/', views.upload_csv, name='upload_csv'),
    path('api/submit-meetings/', views.submit_meetings, name='submit_meetings'),
    path('api/get-meetings/', views.get_meetings, name='get_meetings'),
    path('api/delete-meetings/', views.delete_past_meetings, name='delete_meetings'),
]