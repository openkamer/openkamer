 # -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 19:30:38 2017

@author: stef
"""

import datetime
from haystack import indexes
from document.models import Document, Kamerstuk,Kamervraag

        
class KamerstukIndex(indexes.SearchIndex, indexes.Indexable):
    title = indexes.CharField(model_attr='document')
    text = indexes.CharField(use_template=True,document=True)
    publication_type = indexes.CharField(model_attr='type', faceted=True )
    submitters = indexes.MultiValueField(model_attr='document', faceted=True)
    
    parties= indexes.MultiValueField(model_attr='document', faceted=True)
    dossier = indexes.CharField(model_attr='document', faceted=True)
    decision = indexes.CharField(model_attr='document', faceted=True)
    date = indexes.FacetDateField(model_attr='document')
    
    def prepare_date(self, obj):
        return '' if not obj.document else obj.document.date_published.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_dossier(self,obj):
        return '' if not obj.document else ['' if not obj.document.dossier else obj.document.dossier.dossier_id]
        
    def prepare_decision(self,obj):
        return '' if not obj.document else ['' if not obj.document.dossier else obj.document.dossier.get_status_display() ]
        
        
        

    def prepare_title(self, obj):
        return '' if not obj.document else obj.document.title_short
        
    def prepare_submitters(self, obj):
        return '' if not obj.document else [n.person.fullname() if n.person else '' for n in obj.document.submitters]
    
    def prepare_parties(self, obj):
        return '' if not obj.document else [n.party.name_short if n.party else '' for n in obj.document.submitters]
    
    def get_model(self):
        return Kamerstuk

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
        
class KamervraagIndex(indexes.SearchIndex, indexes.Indexable):
    
    title = indexes.CharField(model_attr='document')
    text = indexes.CharField(use_template=True,document=True)
    publication_type = indexes.CharField(faceted=True)
    submitters = indexes.MultiValueField(model_attr='document', faceted=True)
    
    parties= indexes.MultiValueField(model_attr='document', faceted=True)
    dossier = indexes.CharField(model_attr='document', faceted=True)
    date = indexes.FacetDateField(model_attr='document')
    decision = indexes.CharField(faceted=True)
    receiver = indexes.CharField(model_attr='receiver', faceted=True)
    
    def prepare_receiver(self, obj):
        return obj.receiver
    
    def prepare_decision(self,obj):
        return "Onbeantwoord" if not obj.kamerantwoord else "Beantwoord"
    
    def prepare_publication_type(self,obj):
        return 'Kamervraag'
        
    def prepare_date(self, obj):
        return '' if not obj.document else obj.document.date_published.strftime('%Y-%m-%dT%H:%M:%SZ')

    def prepare_dossier(self,obj):
        return '' if not obj.document else ['' if not obj.document.dossier else obj.document.dossier.dossier_id]

    def prepare_title(self, obj):
        return '' if not obj.document else obj.document.title_short
        
    def prepare_submitters(self, obj):
        if not obj.document: 
            submitters = ''        
        else:
            if obj.kamerantwoord:
                        submitters = [n.person.fullname() if n.person else '' for n in obj.document.submitters|obj.kamerantwoord.document.submitters]
            else:
                        submitters = [n.person.fullname() if n.person else '' for n in obj.document.submitters]
        
        return submitters
    
    def prepare_parties(self, obj):
        return '' if not obj.document else [n.party.name_short if n.party else '' for n in obj.document.submitters]  
    
    def get_model(self):
        return Kamervraag
     
    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

