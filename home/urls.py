from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about', views.About.as_view(), name='about'),
    path('slide/<int:pk>/', views.SlideFileView.as_view(), name='slide_file'),
]