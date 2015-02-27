from django.conf.urls import patterns, include, url
from django.contrib import admin

from website.views import HomeView
from website.views import BillsView

urlpatterns = patterns('',
                       url(r'^$', HomeView.as_view()),
                       url(r'^uitslagen/', BillsView.as_view()),
                       url(r'^admin/', include(admin.site.urls)),
                       )
