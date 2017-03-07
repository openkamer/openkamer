from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from person.views import PersonView
from person.views import PersonsView
from person.views import TwitterPersonsView
from person.views import PersonsCheckView
from document.views import PersonAutocomplete
from document.views import BesluitenLijstView, BesluitenLijstenView
from document.views import DossiersCheckView
from document.views import DossiersView
from document.views import DossierView, AddDossierView
from document.views import DossierTimelineView
from document.views import DossierTimelineHorizontalView
from document.views import AgendasView, AgendaView
from document.views import DocumentView
from document.views import KamerstukView
from document.views import KamerstukRedirectView
from document.views import KamerstukCheckView
from document.views import KamervragenView
from document.views import PersonDocumentsView
from document.views import VotingView
from document.views import VotingsView
from document.views import VotingsCheckView
from government.views import GovernmentsView
from government.views import GovernmentView
from government.views import GovernmentCurrentView
from parliament.views import PartiesView, PartyView, PartyMembersCheckView
from parliament.views import ParliamentMembersCurrentView
from parliament.views import ParliamentMembersAtDateView
from parliament.views import ParliamentMembersCheckView
from stats.views import get_example_plot_html_json
from stats.views import DataStatsView
from stats.views import VotingsPerPartyView

from website.views import DatabaseDumpsView
from website.views import HomeView
from website.views import ContactView
from website import settings
from website.views import get_dossier_timeline_json
from website.views import PlotExampleView

import website.api


urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^colofon/$', TemplateView.as_view(template_name="website/about.html"), name='about'),
    url(r'^contact/$', ContactView.as_view(), name='contact'),

    url(r'^personen/$', PersonsView.as_view(), name='persons'),
    url(r'^personen/twitter/$', TwitterPersonsView.as_view(), name='persons-twitter'),
    url(r'^persoon/(?P<slug>[-\w]+)/$', PersonView.as_view(), name='person'),
    url(r'^person-autocomplete/$', PersonAutocomplete.as_view(), name='person-autocomplete'),

    url(r'^partijen/$', PartiesView.as_view(), name='parties'),
    url(r'^partij/(?P<slug>[-\w]+)/$', PartyView.as_view(), name='party'),

    url(r'^tweedekamerleden/$', ParliamentMembersCurrentView.as_view(), name='parliament-members'),
    url(r'^tweedekamerleden/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', ParliamentMembersAtDateView.as_view(), name='parliament-members-at-date'),

    url(r'^kabinetten/$', GovernmentsView.as_view(), name='governments'),
    url(r'^kabinet/huidig/$', GovernmentCurrentView.as_view(), name='government-current'),
    url(r'^kabinet/(?P<slug>[-\w]+)/$', GovernmentView.as_view(), name='government'),

    url(r'^wetsvoorstellen/$', DossiersView.as_view(), name='wetsvoorstellen'),
    url(r'^dossiers/$', RedirectView.as_view(url='/wetsvoorstellen/', permanent=False)),
    url(r'^dossier/tiles/(?P<dossier_id>\d+)/$', DossierView.as_view(), name='dossier-tiles'),
    url(r'^dossier/tijdlijn/(?P<dossier_id>\d+)/$', DossierTimelineView.as_view(), name='dossier-timeline'),
    url(r'^dossier/tijdlijn/horizontal/(?P<dossier_id>\d+)/$', DossierTimelineHorizontalView.as_view(), name='dossier-timeline-horizontal'),
    url(r'^dossier/timeline/horizontal/json/?', get_dossier_timeline_json),
    url(r'^dossier/add/(?P<dossier_id>\d+)/$', AddDossierView.as_view()),

    url(r'^agendas/$', AgendasView.as_view()),
    url(r'^agenda/(?P<agenda_id>.*)/$', AgendaView.as_view()),

    url(r'^kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>0.*)/$', KamerstukRedirectView.as_view(permanent=True)),
    url(r'^kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>.*)/$', KamerstukView.as_view(), name='kamerstuk'),
    url(r'^kamerstuk/check/$', KamerstukCheckView.as_view(), name='kamerstuk-check'),
    url(r'^document/(?P<document_id>.*)/$', DocumentView.as_view(), name='document'),

    url(r'^kamervragen//$', KamervragenView.as_view(), name='kamervragen'),

    url(r'^persoon/documenten/(?P<person_id>\d+)/$', PersonDocumentsView.as_view(), name='person-documents'),

    url(r'^besluitenlijsten/$', BesluitenLijstenView.as_view(), name='besluitenlijsten'),
    url(r'^besluitenlijst/(?P<activity_id>.*)/$', BesluitenLijstView.as_view(), name='besluitenlijst'),

    url(r'^stemmingen/$', VotingsView.as_view(), name='votings'),
    url(r'^stemming/dossier/(?P<dossier_id>\d+)/$', VotingView.as_view(), name='voting-dossier'),
    url(r'^stemming/kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>.*)/$', VotingView.as_view(), name='voting-kamerstuk'),

    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^stats/$', TemplateView.as_view(template_name='stats/index.html'), name='stats'),
    url(r'^stats/data/$', DataStatsView.as_view(), name='stats-data'),
    url(r'^stats/stemmingen/partijen/$', VotingsPerPartyView.as_view(), name='stats-votings-party'),
    url(r'^stats/exampleplots/$', PlotExampleView.as_view()),
    url(r'^stats/exampleplotjson/?', get_example_plot_html_json),

    url(r'^database/dumps/$', DatabaseDumpsView.as_view(), name='database-dumps'),

    url(r'^checks/$', TemplateView.as_view(template_name='website/checks.html'), name='checks'),
    url(r'^personen/check/$', PersonsCheckView.as_view(), name='persons-check'),
    url(r'^partijleden/check/$', PartyMembersCheckView.as_view(), name='party-members-check'),
    url(r'^tweedekamerleden/check/$', ParliamentMembersCheckView.as_view(), name='parliament-members-check'),
    url(r'^stemmingen/check/$', VotingsCheckView.as_view(), name='votings-check'),
    url(r'^dossiers/check/$', DossiersCheckView.as_view(), name='dossiers-check'),

    url(r'^testlist/$', TemplateView.as_view(template_name="website/testlist.html")),

    url(r'^google9b15c66ff83a61ed.html$', TemplateView.as_view(template_name="website/google9b15c66ff83a61ed.html")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
