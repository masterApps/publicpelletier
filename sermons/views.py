# sermons/views.py - Enhanced with chunked upload API
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, ListView, View
from django.http import Http404, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.db import transaction
import json
import hashlib
import re

from .models import AudioSermon, AudioUploadSession, AudioUploadChunk


class AudioFileView(View):
    """Serve audio files with range request support"""

    def get(self, request, pk):
        sermon = get_object_or_404(AudioSermon, pk=pk)

        if sermon.total_chunks == 0:
            raise Http404("Audio file not found")

        range_header = request.META.get('HTTP_RANGE')

        if range_header:
            return self.handle_range_request(sermon, range_header)
        else:
            return self.handle_full_request(sermon)

    def handle_full_request(self, sermon):
        def chunk_generator():
            chunks = sermon.chunks.order_by('chunk_order')
            for chunk in chunks:
                yield chunk.data

        response = StreamingHttpResponse(
            chunk_generator(),
            content_type=sermon.content_type
        )

        response['Content-Disposition'] = f'inline; filename="{sermon.audio_name}"'
        response['Content-Length'] = str(sermon.audio_size)
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'public, max-age=3600'

        return response

    def handle_range_request(self, sermon, range_header):
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)
        if not range_match:
            return self.handle_full_request(sermon)

        start = int(range_match.group(1))
        end_str = range_match.group(2)
        end = int(end_str) if end_str else sermon.audio_size - 1

        if start >= sermon.audio_size or end >= sermon.audio_size or start > end:
            response = StreamingHttpResponse(
                iter([]),
                status=416,
                content_type=sermon.content_type
            )
            response['Content-Range'] = f'bytes */{sermon.audio_size}'
            return response

        def partial_chunk_generator():
            chunks = sermon.chunks.order_by('chunk_order')
            current_pos = 0

            for chunk in chunks:
                chunk_size = len(chunk.data)
                chunk_end = current_pos + chunk_size - 1

                if chunk_end < start:
                    current_pos += chunk_size
                    continue

                if current_pos > end:
                    break

                chunk_start = max(0, start - current_pos)
                chunk_end_slice = min(chunk_size, end - current_pos + 1)

                if chunk_start < chunk_end_slice:
                    yield chunk.data[chunk_start:chunk_end_slice]

                current_pos += chunk_size

        content_length = end - start + 1

        response = StreamingHttpResponse(
            partial_chunk_generator(),
            status=206,
            content_type=sermon.content_type
        )

        response['Content-Range'] = f'bytes {start}-{end}/{sermon.audio_size}'
        response['Content-Length'] = str(content_length)
        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'public, max-age=3600'

        return response

@method_decorator([login_required, ensure_csrf_cookie], name='dispatch')
class ChunkedUploadInitView(View):
    """Initialize a chunked upload session"""

    def get(self, request):
        return JsonResponse({'Hello': 4})

    def post(self, request):
        try:
            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['filename', 'fileSize', 'contentType', 'chunkSize']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing field: {field}'}, status=400)

            filename = data['filename']
            file_size = int(data['fileSize'])
            content_type = data['contentType']
            chunk_size = int(data['chunkSize'])

            # Calculate total chunks needed
            total_chunks = (file_size + chunk_size - 1) // chunk_size

            # Create upload session
            session = AudioUploadSession.objects.create(
                audio_name=filename,
                content_type=content_type,
                total_size=file_size,
                total_chunks_expected=total_chunks
            )

            return JsonResponse({
                'sessionId': str(session.session_id),
                'totalChunks': total_chunks,
                'chunkSize': chunk_size
            })

        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({'error': 'Invalid request data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ChunkedUploadChunkView(View):
    """Handle individual chunk uploads"""

    def post(self, request, session_id):
        try:
            logging.debug("chunk upload")
            logging.log(1,"ChunkedUploadChunkView")
            session = get_object_or_404(AudioUploadSession, session_id=session_id)

            if session.is_complete:
                return JsonResponse({'error': 'Upload already complete'}, status=400)

            # Get chunk data
            chunk_order = int(request.POST.get('chunkOrder'))
            chunk_file = request.FILES.get('chunk')
            expected_checksum = request.POST.get('checksum', '')  # Optional client-side checksum

            if not chunk_file:
                return JsonResponse({'error': 'No chunk data provided'}, status=400)

            # Verify chunk doesn't already exist
            if session.upload_chunks.filter(chunk_order=chunk_order).exists():
                return JsonResponse({'error': 'Chunk already uploaded'}, status=400)

            # Read and verify chunk data
            chunk_data = chunk_file.read()

            # Verify checksum if provided
            if expected_checksum:
                actual_checksum = hashlib.md5(chunk_data).hexdigest()
                if actual_checksum != expected_checksum:
                    return JsonResponse({'error': 'Checksum mismatch'}, status=400)

            # Save chunk
            with transaction.atomic():
                upload_chunk = AudioUploadChunk.objects.create(
                    session=session,
                    chunk_order=chunk_order,
                    data=chunk_data
                )

                # Update session progress
                session.uploaded_size += len(chunk_data)
                session.save()
                session2 = get_object_or_404(AudioUploadSession, session_id=session_id)
                session2.chunks_received += 1
                print("chunks received:", session2.chunks_received)
                session2.save()

            # Check if upload is complete
            is_complete = session.chunks_received == session.total_chunks_expected

            return JsonResponse({
                'success': True,
                'chunkOrder': chunk_order,
                'chunksReceived': session.chunks_received,
                'totalChunks': session.total_chunks_expected,
                'uploadedSize': session.uploaded_size,
                'totalSize': session.total_size,
                'isComplete': is_complete,
                'checksum': upload_chunk.checksum
            })

        except AudioUploadSession.DoesNotExist:
            return JsonResponse({'error': 'Invalid session ID'}, status=404)
        except (ValueError, KeyError) as e:
            return JsonResponse({'error': 'Invalid request data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ChunkedUploadCompleteView(View):
    """Complete a chunked upload and create sermon"""

    def post(self, request, session_id):
        try:
            session = get_object_or_404(AudioUploadSession, session_id=session_id)
            data = json.loads(request.body)

            # Get sermon metadata
            title = data.get('title', 'Something')
            passage = data.get('passage', 'John 3:16')
            date = data.get('date', '')

            if not all([title, passage]):
                return JsonResponse({'error': 'Title and passage are required'}, status=400)

            # Create sermon
            with transaction.atomic():
                sermon = AudioSermon.objects.create(
                    title=title,
                    passage=passage,
                    date=date if date else None
                )

                session.sermon = sermon
                session.save()
                print("Session Saved!")

                # Complete the upload (this moves chunks to sermon)
                success = session.mark_complete()
                print(success)

                if success:
                    # Clean up upload chunks (they're now copied to sermon chunks)
                    session.upload_chunks.all().delete()

                    return JsonResponse({
                        'success': True,
                        'sermonId': sermon.pk,
                        'message': 'Upload completed successfully'
                    })
                else:
                    return JsonResponse({'error': 'Failed to complete upload'}, status=400)

        except AudioUploadSession.DoesNotExist:
            return JsonResponse({'error': 'Invalid session ID'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(login_required, name='dispatch')
class ChunkedUploadStatusView(View):
    """Check upload status"""

    def get(self, request, session_id):
        try:
            session = get_object_or_404(AudioUploadSession, session_id=session_id)

            return JsonResponse({
                'sessionId': str(session.session_id),
                'filename': session.audio_name,
                'totalSize': session.total_size,
                'uploadedSize': session.uploaded_size,
                'totalChunks': session.total_chunks_expected,
                'chunksReceived': session.chunks_received,
                'isComplete': session.is_complete,
                'createdAt': session.created_at.isoformat(),
                'completedAt': session.completed_at.isoformat() if session.completed_at else None
            })

        except AudioUploadSession.DoesNotExist:
            return JsonResponse({'error': 'Invalid session ID'}, status=404)

class ChunkedUploadView(LoginRequiredMixin, TemplateView):
    """View for the chunked upload form"""
    template_name = 'sermons/audioSermonUpload.html'
    title = "Upload New Sermon"
    active = "upload"

    def get_title(self):
        return self.title

    def get_active(self):
        return self.active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active

        # Add upload configuration
        from django.conf import settings
        chunked_settings = getattr(settings, 'CHUNKED_UPLOAD_SETTINGS', {})

        context["chunk_size"] = chunked_settings.get('CHUNK_SIZE', 1024 * 1024)
        context["max_chunk_size"] = chunked_settings.get('MAX_CHUNK_SIZE', 10 * 1024 * 1024)
        context["max_file_size"] = chunked_settings.get('MAX_FILE_SIZE', 500 * 1024 * 1024)  # 500MB default

        return context

class SermonsList(ListView):
    model = AudioSermon
    context_object_name = "sermons"
    template_name = 'sermons/list.html'
    title = "Recent Sermons"
    active = "sermons"
    ordering = ['-date']

    def get_queryset(self):
        return super().get_queryset().filter(total_chunks__gt=0)

    def get_title(self):
        return self.title

    def get_active(self):
        return self.active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active

        context["total_sermons"] = self.get_queryset().count()
        total_size = sum(sermon.audio_size for sermon in self.get_queryset())
        context["total_size"] = self.format_size(total_size)

        return context

    def format_size(self, size_bytes):
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"