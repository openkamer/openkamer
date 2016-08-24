from django.conf.urls import include, url
from django.contrib import admin

from person.views import PersonsView
from document.views import DossierView, DossiersView, AddDossierView
from document.views import DocumentView
from parliament.views import PartiesView, ParliamentMembersView

from website.views import HomeView
from website.views import BillsView
import website.api


urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^persons/$', PersonsView.as_view()),
    url(r'^parties/$', PartiesView.as_view()),
    url(r'^parliamentmembers/$', ParliamentMembersView.as_view()),
    url(r'^dossiers/$', DossiersView.as_view()),
    url(r'^dossier/(?P<pk>\d+)/$', DossierView.as_view()),
    url(r'^dossier/add/(?P<dossier_id>\d+)/$', AddDossierView.as_view()),
    url(r'^document/(?P<pk>\d+)/$', DocumentView.as_view()),
    url(r'^bills/$', BillsView.as_view()),
    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),
]
