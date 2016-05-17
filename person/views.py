from django.views.generic import TemplateView

from person.models import Person


class PersonsView(TemplateView):
    template_name = 'person/persons.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.all()
        context['persons'] = persons
        return context
