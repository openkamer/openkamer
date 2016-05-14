from django.views.generic import TemplateView

from parliament.models import Person


class PersonsView(TemplateView):
    template_name = 'parliament/persons.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.all()
        for person in persons:
            person.image_url = person.get_image_url()
        context['persons'] = persons
        return context
