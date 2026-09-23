# sermons/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ChunkedUploadView.as_view(), name='chunked_upload'),

    # Chunked upload API endpoints
    path('api/upload/init/', views.ChunkedUploadInitView.as_view(), name='chunked_upload_init'),
    path('api/upload/<uuid:session_id>/chunk/', views.ChunkedUploadChunkView.as_view(), name='chunked_upload_chunk'),
    path('api/upload/<uuid:session_id>/complete/', views.ChunkedUploadCompleteView.as_view(), name='chunked_upload_complete'),
    path('api/upload/<uuid:session_id>/status/', views.ChunkedUploadStatusView.as_view(), name='chunked_upload_status'),
]