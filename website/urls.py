from django.conf.urls import patterns, include, url
from django.contrib import admin

from website.views import HomeView
from website.views import BillsView
from website.views import MembersView

urlpatterns = patterns('',
                       url(r'^$', HomeView.as_view()),
                       url(r'^bills/', BillsView.as_view()),
                       url(r'^kamerleden/', MembersView.as_view()),
                       url(r'^admin/', include(admin.site.urls)),
                       )
