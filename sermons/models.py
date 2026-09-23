# sermons/models.py - Enhanced for chunked uploads
from django.db import models
from django.http import StreamingHttpResponse
from datetime import datetime
import mimetypes
import hashlib
import uuid


class AudioUploadSession(models.Model):
    """Tracks chunked upload sessions"""
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    audio_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    total_size = models.PositiveIntegerField()
    uploaded_size = models.PositiveIntegerField(default=0)
    total_chunks_expected = models.PositiveIntegerField()
    chunks_received = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_complete = models.BooleanField(default=False)

    # Link to sermon once complete
    sermon = models.ForeignKey(
        'AudioSermon',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='upload_sessions'
    )

    def mark_complete(self):
        """Mark upload as complete and create sermon chunks"""
        from django.utils import timezone
        print("chunks received:", self.chunks_received)
        print("chunks expected:", self.total_chunks_expected)
        # Verify all chunks are present
        upload_chunks = self.upload_chunks.order_by('chunk_order')

        if upload_chunks.count() == self.total_chunks_expected:
            print("Chunks received!")
            self.is_complete = True
            # Calculate final hash
            hasher = hashlib.sha256()
            total_size = 0

            for chunk in upload_chunks:
                hasher.update(chunk.data)
                total_size += len(chunk.data)

            # Create sermon audio chunks
            if self.sermon:
                # Clear existing chunks
                self.sermon.chunks.all().delete()

                # Copy upload chunks to sermon chunks
                for upload_chunk in upload_chunks:
                    print("Uploading chunk {}".format(upload_chunk.chunk_order))
                    AudioChunk.objects.create(
                        sermon=self.sermon,
                        chunk_order=upload_chunk.chunk_order,
                        data=upload_chunk.data
                    )

                # Update sermon metadata
                self.sermon.audio_name = self.audio_name
                self.sermon.content_type = self.content_type
                self.sermon.audio_size = total_size
                self.sermon.total_chunks = self.total_chunks_expected
                self.sermon.audio_hash = hasher.hexdigest()

                print("try Save")
                self.sermon.save()
                print("Sermon saved")

            self.is_complete = True
            self.completed_at = timezone.now()
            self.save()

            return True
        return False

    def cleanup_expired(days=1):
        """Clean up expired incomplete upload sessions"""
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)

        expired_sessions = AudioUploadSession.objects.filter(
            created_at__lt=cutoff,
            is_complete=False
        )

        count = expired_sessions.count()
        expired_sessions.delete()
        return count


class AudioUploadChunk(models.Model):
    """Temporary storage for upload chunks"""
    session = models.ForeignKey(
        AudioUploadSession,
        on_delete=models.CASCADE,
        related_name='upload_chunks'
    )
    chunk_order = models.PositiveIntegerField()
    data = models.BinaryField()
    checksum = models.CharField(max_length=64, blank=True)  # MD5 for quick verification
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['session', 'chunk_order']
        ordering = ['chunk_order']

    def save(self, *args, **kwargs):
        # Calculate checksum
        if self.data:
            import hashlib
            self.checksum = hashlib.md5(self.data).hexdigest()
        super().save(*args, **kwargs)


class AudioSermon(models.Model):
    date = models.DateField(default=datetime.now)
    title = models.CharField(max_length=100)
    passage = models.CharField(max_length=100)

    # Audio metadata
    audio_name = models.CharField(max_length=255, blank=True)
    audio_size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=100, default='audio/mpeg')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Hash for integrity checking
    audio_hash = models.CharField(max_length=64, blank=True)
    total_chunks = models.PositiveIntegerField(default=0)

    def save_audio(self, uploaded_file, chunk_size=1024 * 1024):
        """Save an uploaded audio file as chunks (legacy method)"""
        # Clear existing chunks
        self.chunks.all().delete()

        # Save metadata
        self.audio_name = uploaded_file.name
        self.audio_size = uploaded_file.size
        self.content_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0]

        # Calculate hash and save chunks
        hasher = hashlib.sha256()
        chunk_order = 0

        uploaded_file.seek(0)

        while True:
            chunk_data = uploaded_file.read(chunk_size)
            if not chunk_data:
                break

            hasher.update(chunk_data)

            AudioChunk.objects.create(
                sermon=self,
                chunk_order=chunk_order,
                data=chunk_data
            )
            chunk_order += 1

        self.total_chunks = chunk_order
        self.audio_hash = hasher.hexdigest()

    def get_audio_response(self):
        """Return a streaming HttpResponse with the audio data"""

        def chunk_generator():
            chunks = self.chunks.order_by('chunk_order')
            for chunk in chunks:
                yield chunk.data

        response = StreamingHttpResponse(
            chunk_generator(),
            content_type=self.content_type
        )
        response['Content-Disposition'] = f'inline; filename="{self.audio_name}"'
        response['Content-Length'] = str(self.audio_size)
        return response

    def verify_integrity(self):
        """Verify the integrity of the stored chunks"""
        hasher = hashlib.sha256()
        chunks = self.chunks.order_by('chunk_order')

        for chunk in chunks:
            hasher.update(chunk.data)

        return hasher.hexdigest() == self.audio_hash

    def __str__(self):
        return f"{self.title} - {self.passage}"


class AudioChunk(models.Model):
    sermon = models.ForeignKey(
        AudioSermon,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_order = models.PositiveIntegerField()
    data = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['sermon', 'chunk_order']
        ordering = ['chunk_order']

    def __str__(self):
        return f"{self.sermon.title} - Chunk {self.chunk_order}"