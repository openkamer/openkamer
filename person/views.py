from django.views.generic import TemplateView

from person.models import Person
from document.models import Submitter


class PersonsView(TemplateView):
    template_name = 'person/persons.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.all()
        context['persons'] = persons
        return context


class PersonView(TemplateView):
    template_name = 'person/person.html'

    def get_context_data(self, slug, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = Person.objects.get(slug=slug)
        context['list_of_submitters']=Submitter.objects.filter(person=context['person'])
        return context


class PersonsCheckView(TemplateView):
    template_name = 'person/persons_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.all()
        same_name_ids = []
        for person in persons:
            persons_same_name = Person.objects.filter(surname=person.surname)
            if persons_same_name.count() > 1:
                for p in persons_same_name:
                    same_name_ids.append(p.id)
        context['persons_same_surname'] = Person.objects.filter(pk__in=same_name_ids).order_by('surname')
        return context
