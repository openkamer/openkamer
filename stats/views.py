import json
import random
import logging

from django.views.generic import TemplateView
from django.http import HttpResponse

import plotly
from plotly.graph_objs import Scatter, Layout

from person.models import Person

from parliament.models import ParliamentMember
from parliament.models import PoliticalParty
from government.models import GovernmentMember
from government.models import Government

from document.models import BesluitenLijst
from document.models import BesluitItemCase
from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import Vraag
from document.models import Antwoord
from document.models import Voting
from document.models import Vote
from document.models import VoteParty

import stats.util
from stats.filters import PartyVotesFilter
from stats.filters import PartyVoteBehaviour
from stats.models import StatsVotingSubmitter

logger = logging.getLogger(__name__)


class DataStatsView(TemplateView):
    template_name = "stats/data.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['n_dossiers'] = Dossier.objects.all().count()
        context['n_documents'] = Document.objects.all().count()
        context['n_kamerstukken'] = Kamerstuk.objects.all().count()
        context['n_kamervragen'] = Kamervraag.objects.all().count()
        context['n_vragen'] = Vraag.objects.all().count()
        context['n_antwoorden'] = Antwoord.objects.all().count()
        context['n_kamerantwoorden'] = Kamerantwoord.objects.all().count()
        context['n_votings'] = Voting.objects.all().count()
        context['n_votes'] = Vote.objects.all().count()
        context['n_besluitenlijsten'] = BesluitenLijst.objects.all().count()
        context['n_besluiten'] = BesluitItemCase.objects.all().count()
        context['n_parliament_members'] = ParliamentMember.objects.all().count()
        context['n_government_members'] = GovernmentMember.objects.all().count()
        context['n_persons'] = Person.objects.all().count()
        context['page_stats_data'] = True
        return context


class VotingsPerPartyView(TemplateView):
    template_name = "stats/votings_party.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        votes_filter = PartyVotesFilter(self.request.GET, queryset=PartyVoteBehaviour.objects.all())
        n_votes_total = 0
        stats = []
        parties = PoliticalParty.sort_by_current_seats(PoliticalParty.objects.all())
        for party in parties:
            stat = PartyVoteBehaviour.get_stats_party_for_qs(party, votes_filter.qs)
            stats.append(stat)
            n_votes_total += stat['n_votes']
        context['stats'] = stats
        context['n_votes'] = n_votes_total
        context['filter'] = votes_filter
        context['page_stats_votings_parties'] = True
        return context


def get_example_plot_html(number_of_points=30):
    data_x = []
    data_y = []
    for i in range(0, number_of_points):
        data_x.append(i)
        data_y.append(random.randint(-10, 10))
    return plotly.offline.plot(
        figure_or_data={
            "data": [Scatter(x=data_x, y=data_y)],
            "layout": Layout(title="Plot Title")
        },
        show_link=False,
        output_type='div',
        include_plotlyjs=False,
        auto_open=False,
    )


def get_example_plot_html_json(request):
    number_of_points = 10
    if request and 'number-of-points' in request.POST:
        number_of_points = int(request.POST['number-of-points'])
    html = get_example_plot_html(number_of_points)
    response = json.dumps({
        'html': html,
    })
    return HttpResponse(response, content_type='application/json')
