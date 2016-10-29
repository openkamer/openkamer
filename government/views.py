import logging

from django.views.generic import TemplateView

from government.models import Government

logger = logging.getLogger(__name__)


class GovernmentsView(TemplateView):
    template_name = 'government/governments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['governments'] = Government.objects.all()
        return context


class GovernmentView(TemplateView):
    template_name = 'government/government.html'

    def get_context_data(self, slug, **kwargs):
        context = super().get_context_data(**kwargs)
        context['government'] = Government.objects.get(slug=slug)
        return context


class GovernmentCurrentView(TemplateView):
    template_name = 'government/government.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        governments = Government.objects.filter(date_dissolved=None)
        if governments.exists():
            government = governments[0]
            if governments.count() > 1:
                logger.error('more than 1 current government found')
        else:
            government = None
        context['government'] = government
        return context
