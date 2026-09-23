from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.views.generic import ListView, View, DetailView
from django.http import HttpResponse, Http404
from .models import Materials
import markdown

# Create your views here.
class ArticleListView(ListView):
    model = Materials
    context_object_name = "materials"
    template_name = 'materials/list.html'
    title = "Ministry Materials"
    active = "materials"

    def get_title(self):
        return self.title
    
    def get_active(self):
        return self.active
    
    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["title"] = self.get_title
        context["active"] = self.get_active
        return context

class ArticleView(DetailView):
    model = Materials
    template_name = 'materials/detail.html'
    context_object_name = 'article'
    slug_field = 'slug'  # Look up by slug instead of pk
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs: any) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["content_html"] = markdown.markdown(
            self.object.body
        )
        return context

class BlobDownloadView(View):
    def get(self, request, slug):
        material = get_object_or_404(Materials, slug=slug)
        if not material.pdf_data:
            raise Http404("PDF file not found")
        return material.get_pdf_response()

class ArticleEditorView(View):
    def get(self, request, slug):
        return Http404