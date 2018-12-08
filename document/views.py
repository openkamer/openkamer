import datetime
import logging

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from haystack.generic_views import FacetedSearchView
from website.facet import FacetedSearchForm

from dal import autocomplete

from person.models import Person

from parliament.models import PoliticalParty

from document.models import Agenda
from document.models import AgendaItem
from document.models import BesluitenLijst
from document.models import Document, Kamerstuk
from document.models import Dossier
from document.models import Kamervraag
from document.models import Antwoord
from document.models import Submitter
from document.models import Voting
from document.models import VoteParty
from document.filters import DossierFilter
from document.filters import KamervraagFilter
from document.filters import VotingFilter
from document import settings


# TODO: remove dependency on website
from openkamer.dossier import create_or_update_dossier
from website.facet import Facet, FacetItem

logger = logging.getLogger(__name__)


class DocumentView(TemplateView):
    template_name = 'document/document.html'

    def get_context_data(self, document_id, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = Document.objects.filter(document_id=document_id)
        if not documents:
            raise Http404
        context['document'] = documents[0]
        return context


class KamerstukView(TemplateView):
    template_name = 'document/kamerstuk.html'

    def get_context_data(self, dossier_id, sub_id, **kwargs):
        context = super().get_context_data(**kwargs)
        kamerstukken = Kamerstuk.objects.filter(id_main=dossier_id, id_sub=sub_id)
        if not kamerstukken:
            raise Http404
        context['kamerstuk'] = kamerstukken[0]
        return context


class KamerstukRedirectView(RedirectView):
    def get_redirect_url(self, dossier_id, sub_id):
        sub_id = sub_id.lstrip('0')  # remove leading zeros
        return reverse('kamerstuk', args=(dossier_id, sub_id), current_app='document')


class PersonAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        persons = Person.objects.exclude(surname='').order_by('surname')
        person_ids = []
        if self.q:
            for person in persons:
                if self.q.lower() in person.fullname().lower():
                    person_ids.append(person.id)
            return Person.objects.filter(pk__in=person_ids)
        return persons

    def get_result_value(self, result):
        return result.slug


class PartyAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        parties = PoliticalParty.objects.all().order_by('name')
        party_ids = []
        if self.q:
            for party in parties:
                if self.q.lower() in party.name.lower() or self.q.lower() in party.name_short.lower():
                    party_ids.append(party.id)
            return PoliticalParty.objects.filter(pk__in=party_ids)
        return parties

    def get_result_value(self, result):
        return result.slug


class DossiersView(TemplateView):
    template_name = 'document/dossiers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dossier_filter = DossierFilter(self.request.GET, queryset=Dossier.objects.all())
        dossiers_filtered = dossier_filter.qs
        paginator = Paginator(dossier_filter.qs, settings.DOSSIERS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            dossiers = paginator.page(page)
        except PageNotAnInteger:
            dossiers = paginator.page(1)
        except EmptyPage:
            dossiers = paginator.page(paginator.num_pages)
        context['dossiers'] = dossiers
        two_month_ago = datetime.date.today()-datetime.timedelta(days=60)
        context['dossiers_voted'] = dossiers_filtered.filter(voting__is_dossier_voting=True, voting__vote__isnull=False, voting__date__gt=two_month_ago).distinct().order_by('-voting__date')[0:settings.NUMBER_OF_LATEST_DOSSIERS]
        context['filter'] = dossier_filter
        context['n_results'] = dossier_filter.qs.count()
        return context


class DossiersTableView(TemplateView):
    template_name = 'document/dossiers_table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossiers'] = Dossier.objects.all()
        return context


class DossierView(TemplateView):
    template_name = 'document/dossier.html'

    def get_context_data(self, dossier_id, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(dossier_id=dossier_id)
        return context


class TimelineItem(object):
    def __init__(self, obj):
        self.obj = obj

    @staticmethod
    def template_name():
        raise NotImplementedError

    @property
    def date(self):
        raise NotImplementedError


class TimelineKamerstukItem(TimelineItem):
    def __init__(self, obj, besluit_cases=None):
        super().__init__(obj)
        self.besluit_cases = besluit_cases

    @staticmethod
    def template_name():
        return 'document/items/timeline_kamerstuk.html'

    @property
    def date(self):
        return self.obj.document.date_published


class TimelineBesluitItem(TimelineItem):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def template_name():
        return 'document/items/timeline_besluit.html'

    @property
    def date(self):
        return self.obj.besluit_item.besluiten_lijst.date_published


class TimelineKamervraagItem(TimelineItem):
    def __init__(self, obj):
        super().__init__(obj)

    @staticmethod
    def template_name():
        return 'document/items/timeline_kamervraag.html'

    @property
    def date(self):
        return self.obj.document.date_published


class DossierTimelineView(TemplateView):
    template_name = 'document/dossier_timeline.html'

    def get_context_data(self, dossier_id, **kwargs):
        context = super().get_context_data(**kwargs)
        dossier = Dossier.objects.get(dossier_id=dossier_id)
        context['dossier'] = dossier
        timeline_items = []
        besluitenlijst_cases = dossier.besluitenlijst_cases
        to_exclude = []
        for kamerstuk in dossier.kamerstukken:
            besluit_cases = []
            for case in besluitenlijst_cases:
                if kamerstuk in case.related_kamerstukken:
                    besluit_cases.append(case)
            if besluit_cases:
                for case in besluit_cases:
                    to_exclude.append(case.id)
            timeline_items.append(TimelineKamerstukItem(kamerstuk, besluit_cases=besluit_cases))
        besluitenlijst_cases = besluitenlijst_cases.exclude(pk__in=to_exclude)
        for case in besluitenlijst_cases:
            timeline_items.append(TimelineBesluitItem(case))
        timeline_items = sorted(timeline_items, key=lambda items: items.date, reverse=True)
        context['timeline_items'] = timeline_items
        return context


class DossierTimelineHorizontalView(TemplateView):
    template_name = 'document/dossier_timeline_horizontal.html'

    def get_context_data(self, dossier_id, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dossier'] = Dossier.objects.get(dossier_id=dossier_id)
        return context


class AgendasView(TemplateView):
    template_name = 'document/agendas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(Agenda.objects.all(), settings.AGENDAS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            agendas = paginator.page(page)
        except PageNotAnInteger:
            agendas = paginator.page(1)
        except EmptyPage:
            agendas = paginator.page(paginator.num_pages)
        context['agendas'] = agendas
        return context


class AgendaView(TemplateView):
    template_name = 'document/agenda.html'

    def get_context_data(self, agenda_id, **kwargs):
        context = super().get_context_data(**kwargs)
        agendas = Agenda.objects.filter(agenda_id=agenda_id)
        if not agendas:
            raise Http404
        agenda = agendas[0]
        context['agenda'] = agendas
        context['agendaitems'] = AgendaItem.objects.filter(agenda=agenda)
        return context


class VotingView(TemplateView):
    template_name = 'document/voting.html'

    def get_context_data(self, dossier_id, sub_id=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if sub_id:
            kamerstuk = Kamerstuk.objects.get(id_main=dossier_id, id_sub=sub_id)
            voting = kamerstuk.voting
        else:
            dossier = Dossier.objects.get(dossier_id=dossier_id)
            voting = dossier.voting
        context['voting'] = voting
        return context


class VotingsView(TemplateView):
    template_name = 'document/votings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting_filter = VotingFilter(self.request.GET, queryset=Voting.objects.all())
        votings_filtered = voting_filter.qs
        paginator = Paginator(votings_filtered.order_by('-date'), settings.VOTINGS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            votings = paginator.page(page)
        except PageNotAnInteger:
            votings = paginator.page(1)
        except EmptyPage:
            votings = paginator.page(paginator.num_pages)
        context['votings'] = votings
        context['filter'] = voting_filter
        context['n_results'] = votings_filtered.count()
        return context


class BesluitenLijstenView(TemplateView):
    template_name = 'document/besluitenlijsten.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(BesluitenLijst.objects.all(), settings.BESLUITENLIJSTEN_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            besluitenlijsten = paginator.page(page)
        except PageNotAnInteger:
            besluitenlijsten = paginator.page(1)
        except EmptyPage:
            besluitenlijsten = paginator.page(paginator.num_pages)
        context['besluitenlijsten'] = besluitenlijsten
        return context


class BesluitenLijstView(TemplateView):
    template_name = 'document/besluitenlijst.html'

    def get_context_data(self, activity_id, **kwargs):
        context = super().get_context_data(**kwargs)
        context['besluitenlijst'] = BesluitenLijst.objects.get(activity_id=activity_id)
        return context


class DossiersCheckView(TemplateView):
    template_name = 'document/dossiers_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wetsvoorstel_ids = Dossier.get_dossier_ids()
        context['dossiers_no_wetsvoorstel'] = Dossier.objects.exclude(dossier_id__in=wetsvoorstel_ids)
        return context


class VotingsCheckView(TemplateView):
    template_name = 'document/votings_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        votings = Voting.objects.all()
        votings_no_submitters = []
        for voting in votings:
            if not voting.submitters:
                votings_no_submitters.append(voting.id)
        context['votings_no_submitters'] = Voting.objects.filter(id__in=votings_no_submitters)
        return context


class KamerstukCheckView(TemplateView):
    template_name = 'document/kamerstuk_check.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kamerstukken = Kamerstuk.objects.all()
        duplicate_ids = []
        for stuk in kamerstukken:
            if Kamerstuk.objects.filter(id_main=stuk.id_main, id_sub=stuk.id_sub).count() > 1:
                duplicate_ids.append(stuk.id)
        context['duplicate_kamerstuks'] = Kamerstuk.objects.filter(id__in=duplicate_ids)
        return context


class PersonDocumentsView(TemplateView):
    template_name = 'document/person_docs.html'

    def get_context_data(self, person_id, **kwargs):
        context = super().get_context_data(**kwargs)
        person = Person.objects.get(id=person_id)
        submitters = Submitter.objects.filter(person=person)
        context['person'] = person
        documents = Document.objects.filter(submitter__in=submitters)
        context['documents'] = documents
        return context


class KamervragenView(TemplateView):
    template_name = 'document/kamervragen.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kamervraag_filter = KamervraagFilter(self.request.GET, queryset=Kamervraag.objects.all())
        paginator = Paginator(kamervraag_filter.qs, settings.DOSSIERS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            kamervragen = paginator.page(page)
        except PageNotAnInteger:
            kamervragen = paginator.page(1)
        except EmptyPage:
            kamervragen = paginator.page(paginator.num_pages)
        recently_answered = kamervraag_filter.qs.filter(kamerantwoord__isnull=False).order_by('-kamerantwoord__document__date_published')[0:4]
        context['kamervragen'] = kamervragen
        context['kamervragen_answered_recently'] = recently_answered
        context['filter'] = kamervraag_filter
        context['n_results'] = kamervraag_filter.qs.count()
        return context


class KamervragenTableView(TemplateView):
    template_name = 'document/kamervragen_table.html'

    def get_context_data(self, year, **kwargs):
        context = super().get_context_data(**kwargs)
        year = int(year)
        year_begin = datetime.date(year=year, month=1, day=1)
        year_end = datetime.date(year=year+1, month=1, day=1)
        context['year'] = year
        context['kamervragen'] = Kamervraag.objects.filter(document__date_published__gte=year_begin, document__date_published__lt=year_end)
        return context


class KamervraagView(TemplateView):
    template_name = 'document/kamervraag.html'

    def get_context_data(self, vraagnummer, **kwargs):
        context = super().get_context_data(**kwargs)
        kamervragen = Kamervraag.objects.filter(vraagnummer=vraagnummer)
        if not kamervragen:
            raise Http404
        context['kamervraag'] = kamervragen[0]
        return context


class DocumentSearchView(FacetedSearchView):
    facet_fields = ['publication_type', 'submitters','parties','dossier','decision', 'date','receiver']
    form_class = FacetedSearchForm
    template_name = 'search/search.html'
    load_all= False
    
    def parse_Solr_timestamp(self,string):
        date={}
        date['string'] = string
        date['year'] = int(string[0:4])
        date['month'] = int(string[5:7])
        date['day'] = int(string[8:10])
        return date
    
    def create_Solr_timestamp(self,date):
        return date.strftime('%Y-%m-%dT00:00:00Z')
        
    
    def get_queryset(self, **kwargs):
        queryset = super().get_queryset(**kwargs)
        queryset = queryset.models(Kamervraag,Kamerstuk,Person)
        for facet in self.facet_fields:
            queryset = queryset.facet(facet, mincount=1)
            
        kwargs = {
            'hl.tag.pre': '<strong class="highlighted">',
            'hl.tag.post': '</strong>',
            'hl.snippets':1,
            'hl.fl':'text',
            'hl.method':'unified',
            'hl.fragsize':100,
            'hl.defaultSummary':'true',
            'hl.maxAnalyzedChars':1000000
            
        }
        queryset = queryset.highlight(**kwargs)
        return queryset
        
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        selected_facets = self.request.GET.getlist('selected_facets')

        try:
            query = context['query'].replace(" ","+")
        except:
            return context
        
        base_url = "/search?q=" + query
        facetlabels = {'publication_type':'Soort','submitters':'Indieners','parties':'Partij','dossier':'Dossier','decision':'Status', 'receiver':'Vraag gesteld aan'}
        
        for facet in selected_facets:
            base_url += "&selected_facets=" + facet
                   
        try: 
            context['upper']
        except:
            context['upper']=self.parse_Solr_timestamp(self.create_Solr_timestamp(datetime.date.today()))
        
        try: 
            context['lower']
        except:
            context['lower']=self.parse_Solr_timestamp(self.create_Solr_timestamp(Document.objects.all().order_by('date_published')[0].date_published))
        context['today']=self.create_Solr_timestamp(datetime.date.today())
        context['2weeks']=self.create_Solr_timestamp(datetime.date.today()-datetime.timedelta(14))
        context['4weeks']=self.create_Solr_timestamp(datetime.date.today()-datetime.timedelta(28))

        try:
            context['facets']['fields']
        except:
            return context       
            
        f = {}  
        for facet in context['facets']['fields']:
            try:
                f[facet]=Facet(facet, label=facetlabels[facet])
            except:
                f[facet]=Facet(facet) 
            
            d={}
            for item in context['facets']['fields'][facet]:
                i = FacetItem(item[0], item[1], base_url=base_url)                
                i.facet = f[facet]                
                f[facet].list_of_facetitems.append(i)
                d[item[0]]=i
            f[facet].d=d
                
        
        for selected_facet in selected_facets:
            facet=selected_facet.split(':')[0]
            item=":".join(selected_facet.split(':')[1:])
            if not facet == 'date':            
                f[facet].d[item].is_selected=True
            else:
                lower, upper = item.split('_TO_',1)
                context['lower']=self.parse_Solr_timestamp(lower)
                context['upper']=self.parse_Solr_timestamp(upper)
                context['url_without_date']=base_url.replace("&selected_facets=" +selected_facet,"")

        try:
            context['url_without_date']
        except:
            context['url_without_date'] = base_url
        
        context['f']=f  
        context['selected_facets']=selected_facets 
        context['base_url']=base_url
        
        if context.get('is_paginated', True):
            paginator = context.get('paginator')
            num_pages = paginator.num_pages
            current_page = context.get('page_obj')
            page_no = current_page.number
    
            if num_pages <= 11 or page_no <= 6:  
                pages = [x for x in range(1, min(num_pages + 1, 12))]
            elif page_no > num_pages - 6:  
                pages = [x for x in range(num_pages - 10, num_pages + 1)]
            else:  
                pages = [x for x in range(page_no - 5, page_no + 6)]
    
            context.update({'pages': pages})
        

        count=self.queryset.count()
        if count==1:
            context['count']="1 resultaat"
        elif count >1:
            context['count']=str(count) + " resultaten"
        
        return context


class VerslagenAlgemeenOverlegView(TemplateView):
    template_name = 'document/verslagen_algemeen_overleg.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verslagen_all = Kamerstuk.objects.filter(type=Kamerstuk.VERSLAG_AO)
        paginator = Paginator(verslagen_all, settings.DOSSIERS_PER_PAGE)
        page = self.request.GET.get('page')
        try:
            verslagen = paginator.page(page)
        except PageNotAnInteger:
            verslagen = paginator.page(1)
        except EmptyPage:
            verslagen = paginator.page(paginator.num_pages)
        context['verslagen'] = verslagen
        context['n_results'] = verslagen_all.count()
        return context
