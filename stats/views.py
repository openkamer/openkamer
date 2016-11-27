import json
import random

from django.views.generic import TemplateView
from django.http import HttpResponse

import plotly
from plotly.graph_objs import Scatter, Layout

from person.models import Person

from parliament.models import ParliamentMember
from government.models import GovernmentMember

from document.models import BesluitenLijst
from document.models import BesluitItemCase
from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Voting
from document.models import Vote



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
