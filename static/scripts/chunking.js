// static/js/chunked-upload.js - Secure version with CSRF protection and authentication

// CSRF utility functions
function getCSRFToken() {
    const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!tokenElement) {
        console.error('CSRF token not found. Make sure {% csrf_token %} is in your template.');
        return null;
    }
    return tokenElement.value;
}

// Enhanced fetch wrapper with CSRF protection and authentication
async function secureFetch(url, options = {}) {
    const csrfToken = getCSRFToken();

    if (!csrfToken) {
        throw new Error('CSRF token not available');
    }

    // Default headers
    const defaultHeaders = {
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest'
    };

    // Merge headers
    const headers = {
        ...defaultHeaders,
        ...(options.headers || {})
    };

    // For JSON requests, add content-type
    if (options.body && typeof options.body === 'string') {
        headers['Content-Type'] = 'application/json';
    }

    const config = {
        credentials: 'same-origin', // Include cookies for authentication
        ...options,
        headers
    };

    const response = await fetch(url, config);

    // Handle authentication errors
    if (response.status === 401 || response.status === 403) {
        // Redirect to login page
        window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        throw new Error('Authentication required');
    }

    return response;
}

class ChunkedUploader {
    constructor(options = {}) {
        this.chunkSize = options.chunkSize || 1024 * 1024; // 1MB default
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 1000; // 1 second
        this.onProgress = options.onProgress || (() => {});
        this.onComplete = options.onComplete || (() => {});
        this.onError = options.onError || (() => {});

        this.sessionId = null;
        this.file = null;
        this.uploadedChunks = new Set();
        this.isUploading = false;
    }

    async uploadFile(file, sermonData) {
        if (this.isUploading) {
            throw new Error('Upload already in progress');
        }

        this.file = file;
        this.isUploading = true;
        this.uploadedChunks.clear();

        try {
            // Initialize upload session
            await this.initializeUpload();

            // Upload chunks
            await this.uploadChunks();

            // Complete upload
            const result = await this.completeUpload(sermonData);

            this.onComplete(result);
            return result;

        } catch (error) {
            this.onError(error);
            throw error;
        } finally {
            this.isUploading = false;
        }
    }

    async initializeUpload() {
        const url = '/editor/sermons/api/upload/init/';
        const response = await secureFetch(url, {
            method: 'POST',
            body: JSON.stringify({
                filename: this.file.name,
                fileSize: this.file.size,
                contentType: this.file.type,
                chunkSize: this.chunkSize
            })
        });

        console.log('Intended path:', url);
        console.log(response.url);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to initialize upload');
        }

        const data = await response.json();
        this.sessionId = data.sessionId;
        this.totalChunks = data.totalChunks;

        console.log(`Upload initialized: ${this.totalChunks} chunks`);
    }

    async uploadChunks() {
        const promises = [];

        for (let chunkOrder = 0; chunkOrder < this.totalChunks; chunkOrder++) {
            promises.push(this.uploadChunk(chunkOrder));
        }

        // Upload chunks in parallel (you can limit concurrency if needed)
        await Promise.all(promises);
    }

    async uploadChunk(chunkOrder, retryCount = 0) {
        const start = chunkOrder * this.chunkSize;
        const end = Math.min(start + this.chunkSize, this.file.size);
        const chunk = this.file.slice(start, end);

        // Calculate chunk checksum for verification
        const checksum = await this.calculateMD5(chunk);

        const formData = new FormData();
        formData.append('chunk', chunk);
        formData.append('chunkOrder', chunkOrder.toString());
        formData.append('checksum', checksum);

        // Add CSRF token to FormData
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken);
        }

        try {
            const response = await fetch(`/editor/sermons/api/upload/${this.sessionId}/chunk/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                window.location.href = 'editor/login/?next=' + encodeURIComponent(window.location.pathname);
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `Failed to upload chunk ${chunkOrder}`);
            }

            const result = await response.json();
            this.uploadedChunks.add(chunkOrder);

            // Update progress
            this.onProgress({
                chunkOrder,
                chunksUploaded: this.uploadedChunks.size,
                totalChunks: this.totalChunks,
                bytesUploaded: result.uploadedSize,
                totalBytes: this.file.size,
                percentage: (this.uploadedChunks.size / this.totalChunks) * 100
            });

            console.log(`Chunk ${chunkOrder} uploaded successfully`);

        } catch (error) {
            if (retryCount < this.maxRetries) {
                console.log(`Retrying chunk ${chunkOrder} (attempt ${retryCount + 1})`);
                await this.delay(this.retryDelay * (retryCount + 1));
                return this.uploadChunk(chunkOrder, retryCount + 1);
            } else {
                throw new Error(`Failed to upload chunk ${chunkOrder} after ${this.maxRetries} retries: ${error.message}`);
            }
        }
    }

    async completeUpload(sermonData) {
        const response = await secureFetch(`/editor/sermons/api/upload/${this.sessionId}/complete/`, {
            method: 'POST',
            body: JSON.stringify(sermonData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to complete upload');
        }

        return await response.json();
    }

    async getUploadStatus() {
        if (!this.sessionId) {
            throw new Error('No active upload session');
        }

        const response = await secureFetch(`/editor/sermons/api/upload/${this.sessionId}/status/`);

        if (!response.ok) {
            throw new Error('Failed to get upload status');
        }

        return await response.json();
    }

    async calculateMD5(blob) {
        // Use Web Crypto API if available (more secure than CryptoJS)
        if (typeof crypto !== 'undefined' && crypto.subtle) {
            try {
                const arrayBuffer = await blob.arrayBuffer();
                const hashBuffer = await crypto.subtle.digest('MD5', arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (error) {
                console.warn('Web Crypto API MD5 not available, falling back to CryptoJS');
            }
        }

        // Fallback to CryptoJS if available
        if (typeof CryptoJS !== 'undefined') {
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = () => {
                    const arrayBuffer = reader.result;
                    const hash = CryptoJS.MD5(CryptoJS.lib.WordArray.create(arrayBuffer));
                    resolve(hash.toString());
                };
                reader.readAsArrayBuffer(blob);
            });
        }

        // If neither is available, skip checksum
        console.warn('No MD5 implementation available, skipping checksum verification');
        return '';
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    cancel() {
        this.isUploading = false;
        // You could implement cancellation logic here
    }
}

// Usage example for admin interface or custom upload form
class AudioUploadForm {
    constructor(formElement) {
        this.form = formElement;
        this.fileInput = formElement.querySelector('input[type="file"]');
        this.progressBar = formElement.querySelector('.progress-bar');
        this.statusDiv = formElement.querySelector('.upload-status');
        this.submitBtn = formElement.querySelector('button[type="submit"]');

        this.uploader = new ChunkedUploader({
            chunkSize: 2 * 1024 * 1024, // 2MB chunks
            onProgress: this.updateProgress.bind(this),
            onComplete: this.onUploadComplete.bind(this),
            onError: this.onUploadError.bind(this)
        });

        this.setupEventListeners();
        this.validateCSRFToken();
    }

    validateCSRFToken() {
        const token = getCSRFToken();
        if (!token) {
            this.onUploadError(new Error('CSRF token not found. Please refresh the page.'));
            this.setUploading(true); // Disable form
        }
    }

    setupEventListeners() {
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            // Validate file type
            const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/x-m4a'];
            if (!allowedTypes.includes(file.type)) {
                this.onUploadError(new Error('Invalid file type. Please select an audio file.'));
                this.fileInput.value = '';
                return;
            }

            // Validate file size (e.g., max 500MB)
            const maxSize = 500 * 1024 * 1024; // 500MB
            if (file.size > maxSize) {
                this.onUploadError(new Error('File size too large. Maximum size is 500MB.'));
                this.fileInput.value = '';
                return;
            }

            this.updateStatus(`Selected: ${file.name} (${this.formatFileSize(file.size)})`);
        }
    }

    async handleSubmit(event) {
        event.preventDefault();

        const file = this.fileInput.files[0];
        if (!file) {
            this.onUploadError(new Error('Please select a file'));
            return;
        }

        // Validate CSRF token before upload
        if (!getCSRFToken()) {
            this.onUploadError(new Error('Security token missing. Please refresh the page.'));
            return;
        }

        // Get sermon metadata from form
        const formData = new FormData(this.form);
        const sermonData = {
            title: formData.get('title')?.trim(),
            passage: formData.get('passage')?.trim(),
            date: formData.get('date')
        };

        if (!sermonData.title || !sermonData.passage) {
            this.onUploadError(new Error('Title and passage are required'));
            return;
        }

        // Validate title length
        if (sermonData.title.length > 200) {
            this.onUploadError(new Error('Title must be 200 characters or less'));
            return;
        }

        this.setUploading(true);

        try {
            await this.uploader.uploadFile(file, sermonData);
        } catch (error) {
            // Error handling is done in onUploadError callback
        }
    }

    updateProgress(progress) {
        const percentage = Math.round(progress.percentage);

        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
            this.progressBar.textContent = `${percentage}%`;
        }

        this.updateStatus(
            `Uploading... ${percentage}% (${progress.chunksUploaded}/${progress.totalChunks} chunks, ` +
            `${this.formatFileSize(progress.bytesUploaded)}/${this.formatFileSize(progress.totalBytes)})`
        );
    }

    onUploadComplete(result) {
        this.setUploading(false);
        this.updateStatus(`Upload completed successfully! Sermon ID: ${result.sermonId}`, 'success');

        // Reset form
        this.form.reset();

        // Optionally redirect to sermon list or show success message
        setTimeout(() => {
            window.location.href = '/sermons/';
        }, 2000);
    }

    onUploadError(error) {
        this.setUploading(false);
        this.updateStatus(`Error: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }

    updateStatus(message, type = 'info') {
        if (this.statusDiv) {
            this.statusDiv.textContent = message;
            this.statusDiv.className = `upload-status ${type}`;
        }
    }

    setUploading(isUploading) {
        if (this.submitBtn) {
            this.submitBtn.disabled = isUploading;
            this.submitBtn.textContent = isUploading ? 'Uploading...' : 'Upload Sermon';
        }

        if (this.fileInput) {
            this.fileInput.disabled = isUploading;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Helper function for sermon deletion with CSRF protection
async function deleteSermon(sermonId) {
    if (!confirm('Are you sure you want to delete this sermon?')) {
        return;
    }

    try {
        const response = await secureFetch(`/editor/sermons/api/sermons/delete/${sermonId}/`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete sermon');
        }

        const result = await response.json();
        alert(result.message);

        // Remove sermon from DOM or refresh page
        location.reload();
    } catch (error) {
        alert(`Error deleting sermon: ${error.message}`);
    }
}

// Initialize upload form when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('audio-upload-form');
    if (uploadForm) {
        new AudioUploadForm(uploadForm);
    }

    // Add CSRF token refresh functionality for long-running pages
    setInterval(() => {
        const token = getCSRFToken();
        if (!token) {
            console.warn('CSRF token missing, page may need refresh');
        }
    }, 30000); // Check every 30 seconds
});

// Utility function for standalone usage
window.ChunkedUploader = ChunkedUploader;
window.secureFetch = secureFetch;
window.deleteSermon = deleteSermon;