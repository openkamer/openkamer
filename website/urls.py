from django.conf.urls import patterns, include, url
from django.contrib import admin

from person.views import PersonsView

from website.views import HomeView
from website.views import BillsView
from website.views import MembersView
import website.api

urlpatterns = [
    url(r'^$', HomeView.as_view()),
    url(r'^persons/', PersonsView.as_view()),
    url(r'^bills/', BillsView.as_view()),
    url(r'^kamerleden/', MembersView.as_view()),
    url(r'^api/', include(website.api)),
    url(r'^admin/', include(admin.site.urls)),
]
