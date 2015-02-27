from django.conf.urls import patterns, include, url
from django.contrib import admin

from website.views import HomeView

urlpatterns = patterns('',
                       url(r'^$', HomeView.as_view()),
                       url(r'^admin/', include(admin.site.urls)),
                       )
