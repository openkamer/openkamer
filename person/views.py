from django.views.generic import TemplateView

from person.models import Person


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
        same_slug_ids = []
        for person in persons:
            persons_same_slug = Person.objects.filter(slug=person.slug)
            if persons_same_slug.count() > 1:
                for p in persons_same_slug:
                    same_slug_ids.append(p.id)
        context['persons_same_slug'] = Person.objects.filter(pk__in=same_slug_ids).order_by('slug')
        return context
