from django.conf.urls import include, url
from django.contrib import admin

from person.views import PersonsView, PersonView
from document.views import DossiersView
from document.views import DossierView, AddDossierView
from document.views import DossierTimelineView
from document.views import DossierTimelineHorizontalView
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
from website.views import get_dossier_timeline_json
from website.views import PlotExampleView

import website.api


urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^persons/$', PersonsView.as_view()),
    url(r'^person/(?P<person_id>\d+)/$', PersonView.as_view()),

    url(r'^parties/$', PartiesView.as_view()),
    url(r'^party/(?P<party_name_short>.*)/$', PartyView.as_view(), name='party'),
    url(r'^parliamentmembers/$', ParliamentMembersView.as_view()),

    url(r'^governments/$', GovernmentsView.as_view()),
    url(r'^government/current/$', GovernmentCurrentView.as_view()),
    url(r'^government/(?P<government_id>\d+)/$', GovernmentView.as_view()),

    url(r'^dossiers/$', DossiersView.as_view(), name='dossiers'),
    url(r'^dossier/tiles/(?P<dossier_id>\d+)/$', DossierView.as_view(), name='dossier-tiles'),
    url(r'^dossier/timeline/(?P<dossier_id>\d+)/$', DossierTimelineView.as_view(), name='dossier-timeline'),
    url(r'^dossier/timeline/horizontal/(?P<dossier_id>\d+)/$', DossierTimelineHorizontalView.as_view(), name='dossier-timeline-horizontal'),
    url(r'^dossier/timeline/horizontal/json/?', get_dossier_timeline_json),
    url(r'^dossier/add/(?P<dossier_id>\d+)/$', AddDossierView.as_view()),

    url(r'^agendas/$', AgendasView.as_view()),
    url(r'^agenda/(?P<pk>\d+)/$', AgendaView.as_view()),
    url(r'^document/voting/(?P<voting_id>\d+)/$', VotingView.as_view()),
    url(r'^document/(?P<document_id>.*)/$', DocumentView.as_view(), name='document'),
    url(r'^votings/$', VotingsView.as_view(), name='votings'),

    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^stats/exampleplots/', PlotExampleView.as_view()),
    url(r'^stats/exampleplotjson/?', get_example_plot_html_json),
]
