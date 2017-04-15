# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 19:30:38 2017

@author: stef
"""

import datetime
from haystack import indexes
from person.models import Person


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    #text = indexes.CharField(document=True, use_template=True)
    forename = indexes.CharField(model_attr='forename')
    text = indexes.CharField(model_attr='surname',document=True)
    slug = indexes.CharField(model_attr='slug')
    #birthdate = indexes.DateTimeField(model_attr='birthdate')

    def get_model(self):
        return Person

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
