from django.views.generic import TemplateView

from document.models import Document


class PersonsView(TemplateView):
    template_name = 'document/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.all()
        return context