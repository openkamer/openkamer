import logging

from django.db import models

from wikidata import wikidata

from person.models import Person

logger = logging.getLogger(__name__)


class Government(models.Model):
    name = models.CharField(max_length=200)
    date_formed = models.DateField()
    wikidata_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.name)
