from django.conf.urls import include, url
from django.contrib import admin

from person.views import PersonsView, PersonView
from document.views import DossiersView
from document.views import DossierView, AddDossierView
from document.views import DossierTimelineView
from document.views import DossierTimelineHorizontalView
from document.views import AgendasView, AgendaView
from document.views import DocumentView
from document.views import KamerstukView
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
    url(r'^persons/$', PersonsView.as_view(), name='persons'),
    url(r'^persoon/(?P<slug>[-\w]+)/$', PersonView.as_view(), name='person'),

    url(r'^partijen/$', PartiesView.as_view(), name='parties'),
    url(r'^partij/(?P<slug>[-\w]+)/$', PartyView.as_view(), name='party'),
    url(r'^tweedekamerleden/$', ParliamentMembersView.as_view(), name='parliament-members'),

    url(r'^kabinetten/$', GovernmentsView.as_view(), name='governments'),
    url(r'^kabinet/huidig/$', GovernmentCurrentView.as_view(), name='government-current'),
    url(r'^kabinet/(?P<slug>[-\w]+)/$', GovernmentView.as_view(), name='government'),

    url(r'^dossiers/$', DossiersView.as_view(), name='dossiers'),
    url(r'^dossier/tiles/(?P<dossier_id>\d+)/$', DossierView.as_view(), name='dossier-tiles'),
    url(r'^dossier/tijdlijn/(?P<dossier_id>\d+)/$', DossierTimelineView.as_view(), name='dossier-timeline'),
    url(r'^dossier/tijdlijn/horizontal/(?P<dossier_id>\d+)/$', DossierTimelineHorizontalView.as_view(), name='dossier-timeline-horizontal'),
    url(r'^dossier/timeline/horizontal/json/?', get_dossier_timeline_json),
    url(r'^dossier/add/(?P<dossier_id>\d+)/$', AddDossierView.as_view()),

    url(r'^agendas/$', AgendasView.as_view()),
    url(r'^agenda/(?P<pk>\d+)/$', AgendaView.as_view()),
    url(r'^kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>.*)/$', KamerstukView.as_view(), name='kamerstuk'),
    url(r'^document/voting/(?P<voting_id>\d+)/$', VotingView.as_view()),
    url(r'^document/(?P<document_id>.*)/$', DocumentView.as_view(), name='document'),
    url(r'^stemmingen/$', VotingsView.as_view(), name='votings'),

    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^stats/exampleplots/', PlotExampleView.as_view()),
    url(r'^stats/exampleplotjson/?', get_example_plot_html_json),
]
