from django.urls import path

from . import views

urlpatterns = [
    path('create-article', views.ArticleEditorView.as_view(), name='editor-article'),
]