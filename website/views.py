
import logging
logger = logging.getLogger(__name__)

from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "website/index.html"
    context_object_name = "homepage"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        return context


class VotingsView(TemplateView):
    template_name = "website/votings.html"
    context_object_name = "votings"

    def get_context_data(self, **kwargs):
        context = super(VotingsView, self).get_context_data(**kwargs)
        return context