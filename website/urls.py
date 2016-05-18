from django.conf.urls import patterns, include, url
from django.contrib import admin

from person.views import PersonsView
from document.views import DocumentsView, DossiersView
from parliament.views import PartiesView, ParliamentMembersView

from website.views import HomeView
from website.views import BillsView
import website.api


urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^persons/', PersonsView.as_view()),
    url(r'^parties/', PartiesView.as_view()),
    url(r'^parliamentmembers/', ParliamentMembersView.as_view()),
    url(r'^dossiers/', DossiersView.as_view()),
    url(r'^bills/', BillsView.as_view()),
    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),
]
