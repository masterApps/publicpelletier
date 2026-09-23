# sermons/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Original URLs
    path('', views.SermonsList.as_view(), name='sermons'),
#     path('upload/', views.ChunkedUploadView.as_view(), name='chunked_upload'),
    path('audio/<int:pk>/', views.AudioFileView.as_view(), name='audio_file'),

    # Chunked upload API endpoints
#     path('api/upload/init/', views.ChunkedUploadInitView.as_view(), name='chunked_upload_init'),
#     path('api/upload/<uuid:session_id>/chunk/', views.ChunkedUploadChunkView.as_view(), name='chunked_upload_chunk'),
#     path('api/upload/<uuid:session_id>/complete/', views.ChunkedUploadCompleteView.as_view(), name='chunked_upload_complete'),
#     path('api/upload/<uuid:session_id>/status/', views.ChunkedUploadStatusView.as_view(), name='chunked_upload_status'),
]