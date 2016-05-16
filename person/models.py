from datetime import datetime

from django.db import models

import requests


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

    def set_wikidata_info(self):
        search_url = 'https://www.wikidata.org/w/api.php'
        params = {
            'action': 'wbsearchentities',
            'format': 'json',
            'search': self.get_full_name(),
            'language': 'nl',
        }
        response = requests.get(search_url, params)
        results_json = response.json()
        if not results_json['search']:
            print('no wikidata found for ' + str(self.get_full_name()))
            return
        wikidata_id = results_json['search'][0]['id']
        print(wikidata_id)
        self.wikidata_id = wikidata_id
        self.update_wikimedia_info()

    def get_wikidata_url(self):
        return 'https://www.wikidata.org/wiki/Special:EntityData/' + str(self.wikidata_id)

    def update_wikimedia_info(self):
        if not self.wikidata_id:
            return ''
        url = self.get_wikidata_url()
        response = requests.get(url)
        jsondata = response.json()
        jsondata = jsondata['entities'][str(self.wikidata_id)]['claims']
        if 'P569' in jsondata:  # date of birth
            birthdate = jsondata['P569'][0]['mainsnak']['datavalue']['value']['time']
            try:
                birthdate = datetime.strptime(birthdate[1:11], '%Y-%m-%d')
                self.birthdate = birthdate.date()
            except ValueError as error:
                print(error)
        if 'P18' in jsondata:  # image
            filename = jsondata['P18'][0]['mainsnak']['datavalue']['value']
            self.wikimedia_image_name = filename
            self.update_image_url()

    def update_image_url(self):
        if not self.wikimedia_image_name:
            return None
        url = 'https://commons.wikimedia.org/w/api.php'
        params = {
            'action': 'query',
            'titles': 'File:' + self.wikimedia_image_name,
            'prop': 'imageinfo',
            'iiprop': 'url',
            'iiurlwidth': '220',
            'format': 'json',
        }
        response = requests.get(url, params)
        jsondata = response.json()
        pages = jsondata['query']['pages']
        for page in pages.values():
            self.wikimedia_image_url = page['imageinfo'][0]['thumburl']
