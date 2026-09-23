from django.urls import path

from . import views

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='materials'),
    path('<slug:slug>/', views.ArticleView.as_view(), name='article_details'),
    path('download/<slug:slug>/', views.BlobDownloadView.as_view(), name='download_file'),
]