from django.views.generic import TemplateView

from stats.views import get_example_plot_html
from django.utils.safestring import mark_safe


class HomeView(TemplateView):
    template_name = "website/index.html"
    context_object_name = "homepage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PlotExampleView(TemplateView):
    template_name = "website/plot_examples.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plot_html'] = mark_safe(get_example_plot_html())
        return context
