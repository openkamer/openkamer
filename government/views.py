from django.views.generic import TemplateView

from government.models import Government


class GovernmentsView(TemplateView):
    template_name = 'government/governments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['governments'] = Government.objects.all()
        return context

