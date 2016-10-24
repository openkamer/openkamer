import logging
import json

from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import redirect

from document.models import Document, Dossier, Kamerstuk
from document.models import Agenda, AgendaItem
from document.models import Document, Dossier
from document.models import Voting

from website.create import create_or_update_dossier

logger = logging.getLogger(__name__)


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

    def get_context_data(self, dossier_pk, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(id=dossier_pk)
        return context


class DossierTimelineView(TemplateView):
    template_name = 'document/dossier_timeline.html'

    def get_context_data(self, dossier_pk, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(id=dossier_pk)
        return context


class DossierTimelineHorizontalView(TemplateView):
    template_name = 'document/dossier_timeline_horizontal.html'

    def get_context_data(self, dossier_pk, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(id=dossier_pk)
        return context


def get_dossier_timeline_json(request):
    events = []
    dossier = Dossier.objects.get(id=request.POST['dossier_pk'])
    for kamerstuk in dossier.kamerstukken():
        published = kamerstuk.document.date_published
        start_date = {
            'year': published.year,
            'month': published.month,
            'day': published.day
        }
        text = {
            'headline': kamerstuk.type_short,
            'text': kamerstuk.type_long
        }
        event = {
            'start_date': start_date,
            'text': text
        }
        events.append(event)
    timeline_info = {
        'events': events
    }
    timeline_json = json.dumps(timeline_info, sort_keys=True, indent=4)
    # print(timeline_json)
    return HttpResponse(timeline_json, content_type='application/json')


class AgendasView(TemplateView):
    template_name = 'document/agendas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agendas'] = Agenda.objects.all()
        return context


class AgendaView(TemplateView):
    template_name = 'document/agenda.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agenda = Agenda.objects.get(id=self.kwargs['pk'])
        context['agenda'] = agenda
        context['agendaitems'] = AgendaItem.objects.filter(agenda=agenda)
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


class VotingView(TemplateView):
    template_name = 'document/voting.html'

    def get_context_data(self, voting_id, **kwargs):
        context = super().get_context_data(**kwargs)
        voting = Voting.objects.get(id=voting_id)
        context['voting'] = voting
        return context


class VotingsView(TemplateView):
    template_name = 'document/votings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        votings = Voting.objects.all()
        context['votings'] = votings
        return context
