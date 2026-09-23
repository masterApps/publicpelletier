from django.shortcuts import render
from django.views.generic import TemplateView

class InternationalView(TemplateView):
    template_name = 'international/international.html'
    title = "International Ministries"
    active = "international"
    def get_context_data(self, **kwargs):
        context = super(InternationalView, self).get_context_data(**kwargs)

# Create your views here.
class LiberiaView(TemplateView):
    template_name = 'international/liberia.html'
    title = "Liberia Ministry"
    active = "international"
    def get_context_data(self, **kwargs):
        context = super(LiberiaView, self).get_context_data(**kwargs)

class OtherMinistriesView(TemplateView):
    template_name = 'international/others.html'
    title = "Other International Ministries"
    active = "international"
    def get_context_data(self, **kwargs):
        context = super(OtherMinistriesView, self).get_context_data(**kwargs)

