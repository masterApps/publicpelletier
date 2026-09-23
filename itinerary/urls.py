# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ItineraryList.as_view(), name='itinerary.list')
]