from django.views.generic import TemplateView

from person.models import Person
from document.models import Submitter
from parliament.models import ParliamentMember

import datetime
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
        stats=dict()
        context['list_of_parliamentmembers']=ParliamentMember.objects.filter(person=context['person'])
        stats['period']=0
        for n in context['list_of_parliamentmembers']:
            left=n.left
            if left==None:
                left=datetime.datetime.now().date()
                
            
            stats['period']+=(left-n.joined).days
        
        stats['n_of_documents']=len(context['list_of_submitters'])
        stats['docs_per_day']=stats['n_of_documents']/stats['period']*365
        context['stats']=stats
        return context


class TwitterPersonsView(TemplateView):
    template_name = 'person/twitter_users.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        persons = Person.objects.exclude(twitter_username='').order_by('surname')
        context['persons'] = persons
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
