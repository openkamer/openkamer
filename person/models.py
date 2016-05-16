from django.db import models

from wikidata import wikidata


class Person(models.Model):
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, default='')
    birthdate = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikimedia_image_name = models.CharField(max_length=200, blank=True)
    wikimedia_image_url = models.URLField(blank=True)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        fullname = self.forename
        if self.surname_prefix:
            fullname += ' ' + str(self.surname_prefix)
        fullname += ' ' + str(self.surname)
        return fullname

    @staticmethod
    def person_exists(forename, surname):
        return Person.objects.filter(forename=forename, surname=surname).exists()

    def update_info(self):
        wikidata_id = wikidata.search_wikidata_id(self.get_full_name())
        if not wikidata_id:
            return
        print(wikidata_id)
        self.wikidata_id = wikidata_id
        self.birthdate = wikidata.get_birth_date(self.wikidata_id)
        self.wikimedia_image_name = wikidata.get_image_filename(self.wikidata_id)
        self.wikimedia_image_url = wikidata.get_wikimedia_image_url(self.wikimedia_image_name)

    def get_wikidata_url(self):
        return 'https://www.wikidata.org/wiki/Special:EntityData/' + str(self.wikidata_id)
