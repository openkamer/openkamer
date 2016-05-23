from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from document.models import Document, Dossier, create_or_update_dossier


class DocumentsView(TemplateView):
    template_name = 'document/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = Document.objects.all()
        return context


class DocumentView(TemplateView):
    template_name = 'document/document.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document'] = Document.objects.get(id=self.kwargs['pk'])
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


class AddDossierView(TemplateView):
    template_name = 'document/dossier.html'

    def get(self, request, **kwargs):
        super().get(request=request, **kwargs)
        dossiers = Dossier.objects.filter(dossier_id=self.kwargs['dossier_id'])
        if dossiers.exists():
            dossier = dossiers[0]
        else:
            dossier = create_or_update_dossier(self.kwargs['dossier_id'])
        url = '/dossier/' + str(dossier.id) + '/'
        return redirect(url)
        # return HttpResponseRedirect()
