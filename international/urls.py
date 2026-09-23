from django.urls import path

from international import views

urlpatterns = [
    path('/', views.LiberiaView.as_view(), name='liberia'),
    path('/liberia/', views.LiberiaView.as_view(), name='liberia'),
    path('/others/', views.LiberiaView.as_view(), name='liberia'),
]