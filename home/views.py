from django.contrib.auth import logout, login, authenticate
from django.views.generic import TemplateView, ListView
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect, render

from .models import SlideModel
from .forms import ContactForm

from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib import messages

class SlideFileView(View):
    def get(self, request, pk):
        slide = get_object_or_404(SlideModel, pk=pk)
        if not slide.file_data:
            raise Http404("File not found")
        return slide.get_file_response()

# Create your views here.
class HomeView(ListView):
    model = SlideModel
    context_object_name = "carousel"
    template_name = 'home/home.html'
    title = "Mike Pelletier Ministries - Home"
    active = "home"

    def get_title(self):
        return self.title

    def get_active(self):
        return self.active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fixed: Call the methods, don't assign the method objects
        context["title"] = self.get_title()
        context["active"] = self.get_active()

        # Handle form - use existing form if POST with errors, otherwise new form
        if 'form' not in kwargs:
            context['form'] = ContactForm()
        else:
            context['form'] = kwargs['form']
        return context

    def post(self, request, *args, **kwargs):
        # Get the queryset for ListView (needed for template context)
        self.object_list = self.get_queryset()

        form = ContactForm(request.POST)
        if form.is_valid():
            # Get cleaned data
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Prepare email content
            email_subject = f"Contact Form: {subject}"
            email_message = f"""
New message from contact form:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
            """

            try:
                # Send email
                send_mail(
                    email_subject,
                    email_message,
                    settings.EMAIL_HOST_USER,
                    ['judaheddy4christ@icloud.com'],
                    fail_silently=False,
                )

                # Show success message
                messages.success(request, 'Thank you! Your message has been sent successfully.')
                # Fixed: Redirect to same page (home) instead of 'contact'
                return redirect('home')  # Make sure this matches your URL name

            except Exception as e:
                messages.error(request, 'Sorry, there was an error sending your message. Please try again.')
                # Optional: Log the actual error for debugging
                print(f"Email error: {e}")

        # If form is invalid or email failed, re-render with form errors
        return self.render_to_response(self.get_context_data(form=form))

class About(TemplateView):
    template_name = 'home/about.html'
    title = "About Mike Pelletier"
    active = "about"

    def get_title(self):
        return self.title
    
    def get_active(self):
        return self.active
    
    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active
        return context

class Materials(TemplateView):
    template_name = 'home/home.html'
    title = "Ministry Materials"
    active = "marterials"

    def get_title(self):
        return self.title
    
    def get_active(self):
        return self.active
    
    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active
        return context

def login_view(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('meeting_form')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'meeting_form')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')
