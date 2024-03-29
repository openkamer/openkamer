import json
import random
import logging
from urllib.parse import urlparse

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from document.filters import KamervraagFilter
from person.models import Person

from parliament.models import ParliamentMember
from parliament.models import PoliticalParty
from government.models import GovernmentMember

from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import Vraag
from document.models import Antwoord
from document.models import Voting
from document.models import Vote
from document.models import FootNote

from stats.filters import PartyVotesFilter
from stats.filters import PartyVoteBehaviour
from stats.models import Plot


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
        # context['n_besluiten'] = Besluit.objects.all().count()
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


class KamervraagFootnotesView(TemplateView):
    template_name = "stats/kamervraag_footnote_sources.html"
    MIN_MENTIONS_TABLE_DEFAULT = 10
    MAX_ITEMS_PLOT = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kamervraag_filter = KamervraagFilter(self.request.GET, queryset=Kamervraag.objects.all())
        vragen_count = kamervraag_filter.qs.count()

        # optimize query if all kamervragen are queried
        if vragen_count == Kamervraag.objects.count():
            domains = self.get_domains()
        else:
            domains = self.get_domains(kamervraag_filter.qs)

        min_mentions_table = self.MIN_MENTIONS_TABLE_DEFAULT if len(domains) > 50 else 1

        domains_selection = []
        for domain in domains:
            if domain[1] < min_mentions_table:
                break
            domains_selection.append(domain)

        context['plot_html'] = mark_safe(self._create_plot(domains))
        context['domains'] = domains_selection
        context['min_mentions'] = min_mentions_table
        context['filter'] = kamervraag_filter
        context['n_results'] = vragen_count
        return context

    @classmethod
    def _create_plot(cls, domains):
        import plotly.offline
        from plotly.graph_objs import Layout, Bar, Margin

        x = []
        y = []
        for domain in domains:
            if len(x) > cls.MAX_ITEMS_PLOT:
                break
            if domain[0] == 'zoek.officielebekendmakingen.nl':
                continue
            x.append(domain[0])
            y.append(domain[1])
        y = list(reversed(y))
        x = list(reversed(x))
        data = [Bar(
            x=y,
            y=x,
            orientation='h'
        )]
        return plotly.offline.plot(
            figure_or_data={
                "data": data,
                "layout": Layout(
                    title="Vermeldingen per website",
                    autosize=True,
                    height=1200,
                    margin=Margin(
                        l=200,
                        r=50,
                        b=40,
                        t=40,
                        pad=4
                    ),
                )
            },
            show_link=False,
            output_type='div',
            include_plotlyjs=False,
            auto_open=False,
        )

    @staticmethod
    def get_domains(kamervragen=None):
        """ Returns a sorted list of domains and how often they are used in FootNotes """
        if kamervragen is not None:
            document_ids = [kv.document.id for kv in kamervragen]
            footnotes = FootNote.objects.filter(document_id__in=document_ids)
        else:
            footnotes = FootNote.objects
        footnotes = footnotes.exclude(url='')
        domains = {}
        for note in footnotes:
            parsed_url = urlparse(note.url)
            hostname = parsed_url.hostname
            if hostname is None:
                continue
            hostname = hostname.replace('www.', '').replace('m.', '')
            if hostname in domains:
                domains[hostname] += 1
            else:
                domains[hostname] = 1
        domains_sorted = [(k, domains[k]) for k in sorted(domains, key=domains.get, reverse=True)]
        return domains_sorted


class KamervraagStats(TemplateView):
    template_name = "stats/kamervraag.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        KamervraagStats.create_plots_if_needed()
        context['page_stats_kamervraag'] = True
        context['plot_kamervraag_vs_time_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_VS_TIME).html)
        context['plot_kamervraag_vs_time_per_party_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_VS_TIME_PARTY).html)
        context['plot_kamervraag_vs_time_per_party_seats_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_VS_TIME_PARTY_SEATS).html)
        context['plot_kamervraag_reply_times_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_HIST).html)
        context['plot_kamervraag_reply_times_per_party_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_PER_PARTY).html)
        context['plot_kamervraag_reply_times_per_year_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_PER_YEAR).html)
        context['plot_kamervraag_reply_times_contour_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_2DHIST).html)
        # context['plot_party_seats_vs_time_html'] = mark_safe(Plot.objects.get(type=Plot.SEATS_PER_PARTY_VS_TIME).html)
        return context

    @staticmethod
    def create_plots_if_needed():
        plots = Plot.objects.filter(type=Plot.KAMERVRAAG_VS_TIME)
        if not plots.exists():
            Plot.create()


class KamervraagVSTime(TemplateView):
    template_name = "stats/kamervraag_vs_time.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        KamervraagStats.create_plots_if_needed()
        plot_html = Plot.objects.get(type=Plot.KAMERVRAAG_VS_TIME).html
        context['plot_html'] = mark_safe(plot_html)
        return context


class KamervraagReplyTime(TemplateView):
    template_name = "stats/kamervraag_reply_time.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        KamervraagStats.create_plots_if_needed()
        context['plot_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_HIST).html)
        return context


class KamervraagReplyTimeContour(TemplateView):
    template_name = "stats/kamervraag_reply_time_contour.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        KamervraagStats.create_plots_if_needed()
        context['plot_html'] = mark_safe(Plot.objects.get(type=Plot.KAMERVRAAG_REPLY_TIME_2DHIST).html)
        return context


def get_example_plot_html(number_of_points=30):
    import plotly.offline
    from plotly.graph_objs import Scatter, Layout, Bar, Margin

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
