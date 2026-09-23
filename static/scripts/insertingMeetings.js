let meetingCount = 0;

// Get CSRF token from Django
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Add CSRF token to FormData
function addCSRFToFormData(formData) {
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    return formData;
}

// Add a new meeting form
function addMeeting(data = {}) {
    meetingCount++;
    const container = document.getElementById('meetingsContainer');

    // Format today's date for default values
    const today = new Date().toISOString().split('T')[0];

    const meetingDiv = document.createElement('div');
    meetingDiv.className = 'meeting-form';
    meetingDiv.id = `meeting-${meetingCount}`;

    meetingDiv.innerHTML = `
                <h4>Meeting ${meetingCount}</h4>
                <button class="remove-meeting" onclick="removeMeeting(${meetingCount})" title="Remove meeting">×</button>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="date_start-${meetingCount}">Start Date *</label>
                        <input type="date" id="date_start-${meetingCount}" name="date_start" value="${data.date_start || today}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="date_end-${meetingCount}">End Date *</label>
                        <input type="date" id="date_end-${meetingCount}" name="date_end" value="${data.date_end || today}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="location-${meetingCount}">Location *</label>
                        <input type="text" id="location-${meetingCount}" name="location" value="${data.location || ''}" required placeholder="e.g., First Baptist Church">
                    </div>
                    
                    <div class="form-group">
                        <label for="host-${meetingCount}">Host *</label>
                        <input type="text" id="host-${meetingCount}" name="host" value="${data.host || ''}" required placeholder="e.g., John Doe">
                    </div>
                    
                    <div class="form-group">
                        <label for="address-${meetingCount}">Address</label>
                        <input type="text" id="address-${meetingCount}" name="address" value="${data.address || ''}" placeholder="e.g., 123 Main Street">
                    </div>
                    
                    <div class="form-group">
                        <label for="city-${meetingCount}">City</label>
                        <input type="text" id="city-${meetingCount}" name="city" value="${data.city || ''}" placeholder="e.g., New York">
                    </div>
                    
                    <div class="form-group">
                        <label for="phone-${meetingCount}">Phone</label>
                        <input type="tel" id="phone-${meetingCount}" name="phone" value="${data.phone || ''}" placeholder="e.g., 555-1234">
                    </div>
                </div>
            `;

    container.appendChild(meetingDiv);
}

// Remove a meeting
function removeMeeting(id) {
    const meeting = document.getElementById(`meeting-${id}`);
    if (meeting) {
        meeting.remove();
    }
}

// Clear all meetings
function clearAll() {
    if (confirm('Are you sure you want to clear all meetings?')) {
        document.getElementById('meetingsContainer').innerHTML = '';
        meetingCount = 0;
        document.getElementById('meetingsList').style.display = 'none';
    }
}

// Show loading
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

// Hide loading
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Show message
function showMessage(message, type = 'success') {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;

    // Auto-hide after 5 seconds
    setTimeout(() => {
        messagesDiv.innerHTML = '';
    }, 5000);
}

// Handle CSV file upload
document.getElementById('csvFile').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('csv_file', file);
    addCSRFToFormData(formData);

    showLoading();

    fetch('/itinerary/api/upload-csv/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            hideLoading();

            if (data.error) {
                showMessage(data.error, 'danger');
                return;
            }

            // Clear existing meetings
            document.getElementById('meetingsContainer').innerHTML = '';
            meetingCount = 0;

            // Add meetings from CSV
            data.meetings.forEach(meeting => {
                addMeeting(meeting);
            });

            showMessage(`Successfully loaded ${data.count} meetings from CSV!`);
            document.getElementById('csvStatus').innerHTML = `<span style="color: green;">✅ Loaded ${data.count} meetings</span>`;
        })
        .catch(error => {
            hideLoading();
            showMessage('Error uploading CSV file', 'danger');
            console.error('Error:', error);
        });
});

// Submit all meetings
function submitMeetings() {
    console.log("Submitting meetings...")
   const meetingForms = document.querySelectorAll('.meeting-form');

   if (meetingForms.length === 0) {
       showMessage('Please add at least one meeting', 'danger');
       return;
   }

   const meetings = [];

   // meetingForms.forEach((form, index) => {
   //     const formData = new FormData(form);
   //     const meeting = {};
   //
   //     for (const [key, value] of formData.entries()) {
   //         meeting[key] = value;
   //     }
   //
   //     meetings.push(meeting);
   // });

    meetingForms.forEach((form, index) => {
        const meeting = {};

        // Get all input fields within this meeting form
        const inputs = form.querySelectorAll('input');
        inputs.forEach(input => {
            meeting[input.name] = input.value;
        });

        meetings.push(meeting);
    });


    showLoading();

   fetch('/itinerary/api/submit-meetings/', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
           'X-CSRFToken': getCSRFToken(),
       },
       body: JSON.stringify({ meetings: meetings })
   })
       .then(response => response.json())
       .then(data => {
           hideLoading();

           if (data.error) {
               showMessage(data.error, 'danger');
               return;
           }

           let message = `Successfully created ${data.created_count} meetings!`;

           if (data.errors && data.errors.length > 0) {
               message += '<br><br>Errors:<br>' + data.errors.join('<br>');
           }

           showMessage(message, data.errors ? 'danger' : 'success');

           // Optionally clear form after successful submission
           if (!data.errors) {
               setTimeout(() => {
                   clearAll();
               }, 2000);
           }
       })
       .catch(error => {
           hideLoading();
           showMessage('Error submitting meetings', 'danger');
           console.error('Error:', error);
       });
}

// Load and display existing meetings
function loadMeetings() {
    showLoading();

    fetch('/editor/meetings/api/get-meetings/')
        .then(response => response.json())
        .then(data => {
            hideLoading();

            const meetingsList = document.getElementById('meetingsList');
            const meetingsListContent = document.getElementById('meetingsListContent');

            if (data.meetings.length === 0) {
                meetingsListContent.innerHTML = '<p>No meetings found.</p>';
            } else {
                meetingsListContent.innerHTML = data.meetings.map(meeting => `
                        <div class="meeting-item">
                            <h5>${meeting.location} - ${meeting.host}</h5>
                            <div class="meeting-details">
                                <div><strong>Start:</strong> ${meeting.date_start}</div>
                                <div><strong>End:</strong> ${meeting.date_end}</div>
                                <div><strong>Address:</strong> ${meeting.address || 'N/A'}</div>
                                <div><strong>City:</strong> ${meeting.city || 'N/A'}</div>
                                <div><strong>Phone:</strong> ${meeting.phone || 'N/A'}</div>
                            </div>
                        </div>
                    `).join('');
            }

            meetingsList.style.display = 'block';
            meetingsList.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            hideLoading();
            showMessage('Error loading meetings', 'danger');
            console.error('Error:', error);
        });
}

function deleteMeetings() {
    if (confirm('Are you sure you want to delete past meetings?')) {
        showLoading();

        fetch('/editor/meetings/api/delete-meetings/', {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            }
        })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                })
    }
}

// Initialize with one empty meeting
document.addEventListener('DOMContentLoaded', function() {
    addMeeting();
});