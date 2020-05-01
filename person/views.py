from django.views.generic import TemplateView
from haystack.generic_views import SearchView
from haystack.forms import SearchForm
from haystack.query import SearchQuerySet

from person.models import Person


class PersonsView(TemplateView):
    template_name = 'person/persons.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['persons'] = Person.objects.all()
        return context


class PersonView(TemplateView):
    template_name = 'person/person.html'

    def get_context_data(self, slug, **kwargs):
        context = super().get_context_data(**kwargs)
        context['person'] = Person.objects.get(slug=slug)
        return context


class TwitterPersonsView(TemplateView):
    template_name = 'person/twitter_users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.exclude(twitter_username='').order_by('surname')
        context['persons'] = persons
        return context


class PersonsCheckView(TemplateView):
    template_name = 'person/check/persons_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['persons_same_surname'] = Person.same_surname()
        context['persons_surname_only'] = Person.objects.filter(forename='', initials='')
        return context


class PersonSlugCheckView(TemplateView):
    template_name = 'person/check/persons_slug_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        same_slug_ids = []
        persons = Person.objects.all()
        for person in persons:
            persons_same_slug = Person.objects.filter(slug=person.slug)
            if persons_same_slug.count() > 1:
                for p in persons_same_slug:
                    same_slug_ids.append(p.id)
        context['persons_same_slug'] = Person.objects.filter(pk__in=same_slug_ids).order_by('slug')
        return context


class PersonTKIDCheckView(TemplateView):
    template_name = 'person/check/persons_tk_id_check.html'

    @staticmethod
    def get_duplicate_person_tk_ids():
        persons = Person.objects.all()
        duplicate_tk_ids = set()
        for p in persons:
            if not p.tk_id:
                continue
            if Person.objects.filter(tk_id=p.tk_id).count() > 1:
                duplicate_tk_ids.add(p.tk_id)
        return list(duplicate_tk_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        duplicate_tk_ids = self.get_duplicate_person_tk_ids()
        context['duplicate_tk_ids'] = Person.objects.filter(tk_id__in=duplicate_tk_ids).order_by('tk_id')
        return context


class PersonSearchView(SearchView):
    template_name='search/searchperson.html'
    load_all=False
    form_class=SearchForm
    queryset=SearchQuerySet().models(Person)
    
#    def extra_context(self):
#        return {
#            'yourValue': 112,
#        }
