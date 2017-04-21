# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 19:30:38 2017

@author: stef
"""

import datetime
from haystack import indexes
from document.models import Document, Kamerstuk

#
class DocumentIndex(indexes.SearchIndex, indexes.Indexable):
    #text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title_full')
    text = indexes.CharField(use_template=True,document=True)
    #slug = indexes.CharField(model_attr='slug')
    publication_type = indexes.CharField(model_attr='publication_type', faceted=True )
#    date_published = indexes.DateField(model_attr='date_published')


    def get_model(self):
        return Document

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
        
class KamerstukIndex(indexes.SearchIndex, indexes.Indexable):
    #text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='document')
    text = indexes.CharField(use_template=True,document=True)
    publication_type = indexes.CharField(model_attr='type', faceted=True )
    submitters = indexes.MultiValueField(model_attr='document', faceted=True)
    
    parties= indexes.MultiValueField(model_attr='document', faceted=True)
    dossier = indexes.CharField(model_attr='document', faceted=True)
    decision = indexes.CharField(model_attr='document', faceted=True)
    #slug = indexes.CharField(model_attr='slug')
#    publication_type = indexes.CharField(model_attr='document.publication_type', faceted=True )
#    date_published = indexes.DateField(model_attr='date_published')

    def prepare_dossier(self,obj):
        return '' if not obj.document.dossier else obj.document.dossier.dossier_id
        
    def prepare_decision(self,obj):
        return '' if not obj.document.dossier else obj.document.dossier.decision

    def prepare_title(self, obj):
        return '' if not obj.document else obj.document.title_full
        
    def prepare_submitters(self, obj):
        return '' if not obj.document else [n.person.fullname() for n in obj.document.submitters]
    
    def prepare_parties(self, obj):
        return '' if not obj.document else [n.party.name_short for n in obj.document.submitters]
    
    def get_model(self):
        return Kamerstuk

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
        

