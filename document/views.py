from django.views.generic import TemplateView

from document.models import Document, Dossier


class DocumentsView(TemplateView):
    template_name = 'document/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.all()
        return context


class DossiersView(TemplateView):
    template_name = 'document/dossiers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossiers'] = Dossier.objects.all()
        return context


class DossierView(TemplateView):
    template_name = 'document/dossier.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(id=self.kwargs['pk'])
        return context