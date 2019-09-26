from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from person.views import PersonView
from person.views import PersonSearchView
from person.views import PersonsView
from person.views import TwitterPersonsView
from person.views import PersonsCheckView
from document.views import PersonAutocomplete
from document.views import PartyAutocomplete
from document.views import BesluitenLijstView, BesluitenLijstenView
from document.views import DocumentSearchView
from document.views import DossiersView
from document.views import DossiersTableView
from document.views import DossierView
from document.views import DossierTimelineView
from document.views import DossierTimelineHorizontalView
from document.views import AgendasView, AgendaView
from document.views import DocumentView
from document.views import KamerstukView
from document.views import KamerstukRedirectView
from document.views import KamerstukCheckView
from document.views import KamervragenView
from document.views import KamervragenTableView
from document.views import KamervraagView
from document.views import PersonDocumentsView
from document.views import VotingView
from document.views import VotingsView
from document.views import VotingsCheckView
from document.views import VerslagenAlgemeenOverlegView
from government.views import GovernmentsView
from government.views import GovernmentView
from government.views import GovernmentCurrentView
from parliament.views import PartiesView, PartyView, PartyMembersCheckView
from parliament.views import ParliamentMembersCurrentView
from parliament.views import ParliamentMembersAtDateView
from parliament.views import ParliamentMembersCheckView
from parliament.views import CommissieView
from stats.views import get_example_plot_html_json
from stats.views import DataStatsView
from stats.views import KamervraagFootnotesView
from stats.views import VotingsPerPartyView
from stats.views import KamervraagStats
from stats.views import KamervraagVSTime
from stats.views import KamervraagReplyTime
from stats.views import KamervraagReplyTimeContour
import gift.views
import travel.views

from website.views import DatabaseDumpsView
from website.views import PersonTimelineView
from website.views import HomeView
from website.views import ContactView
from website import settings
from website.views import get_dossier_timeline_json
from website.views import get_person_timeline_html
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
    url(r'^persoon/tijdlijn/(?P<slug>[-\w]+)/(?P<year>[\d{4}]+)/$', PersonTimelineView.as_view(), name='person-timeline-year'),
    url(r'^persoon/tijdlijn/?', get_person_timeline_html, name='get-person-timeline-html'),

    url(r'^partijen/$', PartiesView.as_view(), name='parties'),
    url(r'^partij/(?P<slug>[-\w]+)/$', PartyView.as_view(), name='party'),
    url(r'^party-autocomplete/$', PartyAutocomplete.as_view(), name='party-autocomplete'),

    url(r'^tweedekamerleden/$', ParliamentMembersCurrentView.as_view(), name='parliament-members'),
    url(r'^tweedekamerleden/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', ParliamentMembersAtDateView.as_view(), name='parliament-members-at-date'),

    url(r'^kabinetten/$', GovernmentsView.as_view(), name='governments'),
    url(r'^kabinet/huidig/$', GovernmentCurrentView.as_view(), name='government-current'),
    url(r'^kabinet/(?P<slug>[-\w]+)/$', GovernmentView.as_view(), name='government'),

    url(r'^wetsvoorstellen/$', DossiersView.as_view(), name='wetsvoorstellen'),
    url(r'^wetsvoorstellen/tabel/$', DossiersTableView.as_view(), name='wetsvoorstellen-table'),
    url(r'^dossiers/$', RedirectView.as_view(url='/wetsvoorstellen/', permanent=False)),
    url(r'^dossier/tiles/(?P<dossier_id>\d+)/$', DossierView.as_view(), name='dossier-tiles'),
    url(r'^dossier/tijdlijn/(?P<dossier_id>\d+)/$', DossierTimelineView.as_view(), name='dossier-timeline'),
    url(r'^dossier/tijdlijn/horizontal/(?P<dossier_id>\d+)/$', DossierTimelineHorizontalView.as_view(), name='dossier-timeline-horizontal'),
    url(r'^dossier/timeline/horizontal/json/?', get_dossier_timeline_json),

    url(r'^agendas/$', AgendasView.as_view()),
    url(r'^agenda/(?P<agenda_id>.*)/$', AgendaView.as_view()),

    url(r'^kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>0.*)/$', KamerstukRedirectView.as_view(permanent=True)),
    url(r'^kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>.*)/$', KamerstukView.as_view(), name='kamerstuk'),
    url(r'^kamerstuk/check/$', KamerstukCheckView.as_view(), name='kamerstuk-check'),
    url(r'^document/(?P<document_id>.*)/$', DocumentView.as_view(), name='document'),

    url(r'^kamervragen/$', KamervragenView.as_view(), name='kamervragen'),
    url(r'^kamervragen/tabel/(?P<year>\d{4})/$', KamervragenTableView.as_view(), name='kamervragen-table'),
    url(r'^kamervraag/(?P<vraagnummer>.*)/$', KamervraagView.as_view(), name='kamervraag'),

    url(r'^commissie/verslagen/$', VerslagenAlgemeenOverlegView.as_view(), name='verslagen-algemeen-overleg'),
    # url(r'^commissies/$', CommissiesView.as_view(), name='commissies'),
    url(r'^commissie/(?P<slug>[-\w]+)/$', CommissieView.as_view(), name='commissie'),

    url(r'^persoon/documenten/(?P<person_id>\d+)/$', PersonDocumentsView.as_view(), name='person-documents'),

    url(r'^besluitenlijsten/$', BesluitenLijstenView.as_view(), name='besluitenlijsten'),
    url(r'^besluitenlijst/(?P<activity_id>.*)/$', BesluitenLijstView.as_view(), name='besluitenlijst'),

    url(r'^stemmingen/$', VotingsView.as_view(), name='votings'),
    url(r'^stemming/dossier/(?P<dossier_id>\d+)/$', VotingView.as_view(), name='voting-dossier'),
    url(r'^stemming/kamerstuk/(?P<dossier_id>\d+)/(?P<sub_id>.*)/$', VotingView.as_view(), name='voting-kamerstuk'),

    url(r'^geschenken/$', gift.views.GiftsView.as_view(), name='gifts'),
    url(r'^reizen/$', travel.views.TravelsView.as_view(), name='travels'),

    url(r'^stats/$', TemplateView.as_view(template_name='stats/index.html'), name='stats'),
    url(r'^stats/data/$', DataStatsView.as_view(), name='stats-data'),
    url(r'^stats/stemmingen/partijen/$', VotingsPerPartyView.as_view(), name='stats-votings-party'),
    url(r'^stats/exampleplots/$', PlotExampleView.as_view()),
    url(r'^stats/exampleplotjson/?', get_example_plot_html_json),
    url(r'^stats/kamervraag/$', KamervraagStats.as_view(), name='stats-kamervraag'),
    url(r'^stats/kamervraag/voetnoot/bron/$', KamervraagFootnotesView.as_view(), name='stats-kamervraag-sources'),
    url(r'^stats/kamervraag/vs/tijd/$', KamervraagVSTime.as_view(), name='stats-kamervraag-vs-time'),
    url(r'^stats/kamervraag/antwoordtijd/$', KamervraagReplyTime.as_view(), name='stats-kamervraag-reply-time'),
    url(r'^stats/kamervraag/antwoordtijd/contour/$', KamervraagReplyTimeContour.as_view(), name='stats-kamervraag-reply-time-contour'),

    url(r'^database/dumps/$', DatabaseDumpsView.as_view(), name='database-dumps'),

    url(r'^checks/$', TemplateView.as_view(template_name='website/checks.html'), name='checks'),
    url(r'^testlist/$', TemplateView.as_view(template_name='website/testlist.html'), name='testlist'),

    url(r'^personen/check/$', PersonsCheckView.as_view(), name='persons-check'),
    url(r'^partijleden/check/$', PartyMembersCheckView.as_view(), name='party-members-check'),
    url(r'^tweedekamerleden/check/$', ParliamentMembersCheckView.as_view(), name='parliament-members-check'),
    url(r'^stemmingen/check/$', VotingsCheckView.as_view(), name='votings-check'),

    url(r'^api/', include(website.api)),
    url(r'^admin/', admin.site.urls),

    url(r'^google9b15c66ff83a61ed.html$', TemplateView.as_view(template_name="website/google9b15c66ff83a61ed.html")),
    url(r'^privacy/english/$', TemplateView.as_view(template_name="website/privacy_policy_english.html")),

    url(r'^personen/search/',PersonSearchView.as_view(), name="search-person"),
    url(r'^search/', DocumentSearchView.as_view(), name="search"),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
