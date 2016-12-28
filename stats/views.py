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

from document.models import BesluitenLijst
from document.models import BesluitItemCase
from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Voting
from document.models import Vote
from document.models import VoteParty

import stats.util
from stats.filters import PartyVotesFilter
from stats.filters import PartyVoteBehaviour

logger = logging.getLogger(__name__)


class DataStatsView(TemplateView):
    template_name = "stats/data.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['n_dossiers'] = Dossier.objects.all().count()
        context['n_documents'] = Document.objects.all().count()
        context['n_kamerstukken'] = Kamerstuk.objects.all().count()
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
        votes_filtered = votes_filter.qs
        votes_filtered.distinct()
        logger.info(votes_filtered.count())
        results = []
        parties = PoliticalParty.sort_by_current_seats(PoliticalParty.objects.all())
        n_votes_total = 0
        for party in parties:
            vote_behaviour = votes_filtered.filter(party=party)
            logger.info(str(party) + ': ' + str(vote_behaviour.count()))
            n_votes_for = 0
            n_votes_against = 0
            n_votes_none = 0
            for result in vote_behaviour:
                n_votes_for += result.votes_for
                n_votes_against += result.votes_against
                n_votes_none += result.votes_none
            n_votes = n_votes_for + n_votes_against + n_votes_none
            n_votes_total += n_votes
            if n_votes == 0:
                for_percent = 0
                against_percent = 0
                none_percent = 0
            else:
                for_percent = n_votes_for/n_votes*100.0
                against_percent = n_votes_against/n_votes*100.0
                none_percent = n_votes_none/n_votes*100.0
            results.append({
                'party': party,
                'n_votes': n_votes,
                'n_for': n_votes_for,
                'n_against': n_votes_against,
                'n_none': n_votes_for,
                'for_percent': for_percent,
                'against_percent': against_percent,
                'none_percent': none_percent,
            })
        context['stats'] = results
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
