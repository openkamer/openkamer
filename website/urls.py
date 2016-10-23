from django.conf.urls import include, url
from django.contrib import admin

from person.views import PersonsView, PersonView
from document.views import DossiersView
from document.views import DossierView, AddDossierView
from document.views import DossierTimelineView
from document.views import AgendasView, AgendaView
from document.views import DocumentView
from document.views import VotingView
from document.views import VotingsView
from government.views import GovernmentsView
from government.views import GovernmentView
from government.views import GovernmentCurrentView
from parliament.views import PartiesView, PartyView
from parliament.views import ParliamentMembersView
from stats.views import get_example_plot_html_json

from website.views import HomeView
from website.views import PlotExampleView
import website.api


urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^persons/$', PersonsView.as_view()),
    url(r'^person/(?P<person_id>\d+)/$', PersonView.as_view()),

    url(r'^parties/$', PartiesView.as_view()),
    url(r'^party/(?P<party_id>\d+)/$', PartyView.as_view()),
    url(r'^parliamentmembers/$', ParliamentMembersView.as_view()),

    url(r'^governments/$', GovernmentsView.as_view()),
    url(r'^government/current/$', GovernmentCurrentView.as_view()),
    url(r'^government/(?P<government_id>\d+)/$', GovernmentView.as_view()),

    url(r'^dossiers/$', DossiersView.as_view()),
    url(r'^agendas/$', AgendasView.as_view()),
    url(r'^agenda/(?P<pk>\d+)/$', AgendaView.as_view()),
    url(r'^dossier/(?P<dossier_pk>\d+)/$', DossierView.as_view()),
    url(r'^dossier/timeline/(?P<dossier_pk>\d+)/$', DossierTimelineView.as_view()),
    url(r'^dossier/add/(?P<dossier_id>\d+)/$', AddDossierView.as_view()),
    url(r'^document/(?P<pk>\d+)/$', DocumentView.as_view()),
    url(r'^document/voting/(?P<voting_id>\d+)/$', VotingView.as_view()),
    url(r'^votings/$', VotingsView.as_view()),

    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^stats/exampleplots/', PlotExampleView.as_view()),
    url(r'^stats/exampleplotjson/?', get_example_plot_html_json),
]
