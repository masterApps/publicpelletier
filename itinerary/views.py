from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView
from django.utils.timezone import now
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import csv
import io
from datetime import datetime
from .models import Meetings

# Create your views here.
class ItineraryList(ListView):
    model = Meetings
    context_object_name = "meetings"
    template_name = 'meetings/meeting_list.html'
    title = "Travel Itinerary"
    active = "itinerary"
    today = now().date()
    ordering =['date_start']

    def get_title(self):
        return self.title
    
    def get_active(self):
        return self.active
    
    def get_today(self):
        return self.today
    
    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active
        context["today"] = self.get_today
        return context

def meeting_form(request):
    """Main form page for multiple meeting submission"""
    return render(request, 'meetings/form.html')


@login_required
@require_http_methods(["POST"])
def upload_csv(request):
    """Handle CSV file upload and return parsed data"""
    if 'csv_file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    csv_file = request.FILES['csv_file']

    if not csv_file.name.endswith('.csv'):
        return JsonResponse({'error': 'File must be a CSV'}, status=400)

    try:
        # Read and decode the CSV file
        decoded_file = csv_file.read().decode('utf-8')
        csv_data = csv.DictReader(io.StringIO(decoded_file))

        meetings = []
        for row in csv_data:
            # Clean and validate data
            meeting_data = {
                'date_start': row.get('date_start', '').strip(),
                'date_end': row.get('date_end', '').strip(),
                'location': row.get('location', '').strip(),
                'host': row.get('host', '').strip(),
                'address': row.get('address', '').strip(),
                'city': row.get('city', '').strip(),
                'phone': row.get('phone', '').strip()
            }
            # print(meeting_data)
            meetings.append(meeting_data)

        return JsonResponse({'meetings': meetings, 'count': len(meetings)})

    except Exception as e:
        return JsonResponse({'error': f'Error processing CSV: {str(e)}'}, status=400)


@login_required
@require_http_methods(["POST"])
def submit_meetings(request):
    """Handle multiple meeting submission"""
    print('Submitting meetings')
    try:
        data = json.loads(request.body)
        meetings_data = data.get('meetings', [])

        if not meetings_data:
            return JsonResponse({'error': 'No meetings provided'}, status=400)

        created_meetings = []
        errors = []

        for i, meeting_data in enumerate(meetings_data):
            try:
                # Validate required fields
                if not meeting_data.get('location'):
                    errors.append(f'Meeting {i + 1}: Location is required')
                    continue

                if not meeting_data.get('host'):
                    errors.append(f'Meeting {i + 1}: Host is required')
                    continue

                # Parse dates
                date_start = meeting_data.get('date_start')
                date_end = meeting_data.get('date_end')

                # Convert date strings to date objects if provided
                if date_start:
                    try:
                        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f'Meeting {i + 1}: Invalid start date format. Use YYYY-MM-DD')
                        continue
                else:
                    date_start = datetime.now().date()

                if date_end:
                    try:
                        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
                    except ValueError:
                        errors.append(f'Meeting {i + 1}: Invalid end date format. Use YYYY-MM-DD')
                        continue
                else:
                    date_end = datetime.now().date()

                # Create meeting
                meeting = Meetings.objects.create(
                    date_start=date_start,
                    date_end=date_end,
                    location=meeting_data['location'],
                    host=meeting_data['host'],
                    address=meeting_data.get('address', ''),
                    city=meeting_data.get('city', ''),
                    phone=meeting_data.get('phone', '')
                )

                created_meetings.append({
                    'id': meeting.id,
                    'location': meeting.location,
                    'host': meeting.host,
                    'date_start': meeting.date_start.strftime('%Y-%m-%d'),
                    'date_end': meeting.date_end.strftime('%Y-%m-%d')
                })

            except Exception as e:
                errors.append(f'Meeting {i + 1}: {str(e)}')

        response_data = {
            'success': True,
            'created_count': len(created_meetings),
            'created_meetings': created_meetings
        }

        if errors:
            response_data['errors'] = errors

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["GET"])
def get_meetings(request):
    """Get all meetings for display"""
    meetings = Meetings.objects.all().order_by('-date_start')
    meetings_data = []

    for meeting in meetings:
        meetings_data.append({
            'id': meeting.id,
            'date_start': meeting.date_start.strftime('%Y-%m-%d'),
            'date_end': meeting.date_end.strftime('%Y-%m-%d'),
            'location': meeting.location,
            'host': meeting.host,
            'address': meeting.address,
            'city': meeting.city,
            'phone': meeting.phone
        })

    return JsonResponse({'meetings': meetings_data})

@login_required
@require_http_methods(["DELETE"])
def delete_past_meetings(request):
    """Delete meeting"""
    meetings = Meetings.objects.all().order_by('-date_start')
    today = datetime.now().date()
    for meeting in meetings:
        if meeting.date_end < today:
            meeting.delete()
    return JsonResponse({'success': True})
