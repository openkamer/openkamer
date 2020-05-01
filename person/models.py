import logging
from unidecode import unidecode

from django.db import models
from django.utils.text import slugify

from wikidata import wikidata

import scraper.persons

logger = logging.getLogger(__name__)


NAME_PREFIXES = [
    'van der',
    'van den',
    'van de',
    'van \'t',
    'in het',
    'van',
    'von',
    'de',
    'het',
    '\'t',
    'der',
    'den',
    'ter',
    'ten',
    'te',
]


class Person(models.Model):
    forename = models.CharField(max_length=200, db_index=True, blank=True)
    surname = models.CharField(max_length=200, db_index=True)
    surname_prefix = models.CharField(max_length=200, blank=True, default='', db_index=True)
    initials = models.CharField(max_length=200, blank=True, default='', db_index=True)
    slug = models.SlugField(max_length=250, default='', blank=True)
    birthdate = models.DateField(blank=True, null=True)
    tk_id = models.CharField(max_length=200, blank=True, db_index=True)
    wikidata_id = models.CharField(max_length=200, blank=True, db_index=True)
    wikipedia_url = models.URLField(blank=True, max_length=1000)
    wikimedia_image_name = models.CharField(blank=True, max_length=300)
    wikimedia_image_url = models.URLField(blank=True, max_length=1000)
    parlement_and_politiek_id = models.CharField(max_length=200, blank=True, db_index=True)
    twitter_username = models.CharField(max_length=200, blank=True)
    datetime_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_full_name() + ' (' + self.initials + ')'

    def save(self, *args, **kwargs):
        name = self.fullname()
        if name.strip() == '':
            name = 'unknown'
        self.slug = slugify(name)
        super().save(*args, **kwargs)

    @staticmethod
    def find_prefix(name):
        # WARNING: does NOT work for prefix after the surname, for example, 'Ham, van der'.
        for prefix in NAME_PREFIXES:
            prefix_pos = name.find(prefix + ' ')
            if prefix_pos >= 0 and (prefix_pos == 0 or name[prefix_pos-1] == ' '):  # prefix must be at the start or there should be a whitespace in front
                name_prefix = prefix
                return name_prefix, prefix_pos
        return '', -1

    @staticmethod
    def find_surname_initials(surname, initials='', persons=None):
        # TODO: improve performance; use queries
        surname = unidecode(surname)
        initials = unidecode(initials)
        persons = persons if persons is not None else Person.objects.all()
        best_match = None
        best_score = 0
        for person in persons:
            score = 0
            surname_no_second = surname.split('-')[0].lower()  # for example, Anne-Wil Lucas-Smeerdijk is called Anne-Wil Lucas on tweedekamer.nl
            person_surname_no_second = person.surname.split('-')[0].lower()
            if surname_no_second == unidecode(person_surname_no_second):
                score += 1
            elif surname_no_second == unidecode(person_surname_no_second + ' ' + person.surname_prefix.lower()):
                score += 1
            elif surname_no_second == unidecode(person.surname_prefix.lower() + ' ' + person_surname_no_second):
                score += 1
            initials_letters = initials.split('.')
            forename = unidecode(person.forename)
            if initials and initials.lower() == unidecode(person.initials.lower()):
                score += 1
            elif initials_letters and forename and initials_letters[0] == forename[0]:
                score += 0.5
            if person.initials and person.forename and person.surname:
                score += 0.1
            if person.wikidata_id:
                score += 0.05
            if score >= 1.5 and score > best_score:
                best_match = person
                best_score = score
        if not best_match:
            logger.info('person not found: ' + surname + ', ' + initials)
        return best_match

    @staticmethod
    def find_by_fullname(fullname):
        persons = Person.objects.all()
        for person in persons:
            if person.fullname().lower() == fullname.lower():
                return person
        return None

    def fullname(self):
        return self.get_full_name()

    def get_full_name(self):
        fullname = ''
        if self.forename:
            fullname = self.forename + ' '
        fullname += self.surname_including_prefix()
        return fullname

    def surname_including_prefix(self):
        if self.surname_prefix:
            return self.surname_prefix + ' ' + self.surname
        return self.surname

    @staticmethod
    def person_exists(forename, surname):
        return Person.objects.filter(forename=forename, surname=surname).exists()

    @staticmethod
    def update_persons_all(language):
        persons = Person.objects.all().order_by('surname')
        for person in persons:
            person.update_info(language=language)
            person.save()

    def find_wikidata_id(self, language='nl'):
        wikidata_id = wikidata.search_wikidata_id(self.get_full_name(), language)
        logger.info('wikidata id: ' + str(wikidata_id))
        return wikidata_id

    def update_info(self, language='nl', wikidata_item=None):
        logger.info('get info from wikidata for ' + str(self.get_full_name()))
        if not self.wikidata_id:
            self.wikidata_id = self.find_wikidata_id(language)
        if not self.wikidata_id:
            logger.warning('no wikidata id found')
            return
        if not wikidata_item:
            wikidata_item = wikidata.WikidataItem(self.wikidata_id)
        birthdate = wikidata_item.get_birth_date()
        if birthdate:
            self.birthdate = birthdate
        self.wikipedia_url = wikidata_item.get_wikipedia_url(language)
        image_filename = wikidata_item.get_image_filename()
        if image_filename:
            self.wikimedia_image_name = image_filename
            self.wikimedia_image_url = wikidata.WikidataItem.get_wikimedia_image_url(self.wikimedia_image_name)
        self.parlement_and_politiek_id = wikidata_item.get_parlement_and_politiek_id()
        if self.parlement_and_politiek_id and not self.initials:
            self.initials = scraper.persons.get_initials(self.parlement_and_politiek_id)
        self.twitter_username = wikidata_item.get_twitter_username()

    def wikidata_url(self):
        return 'https://www.wikidata.org/wiki/Special:EntityData/' + str(self.wikidata_id)

    def parlement_and_politiek_url(self):
        return 'https://www.parlement.com/id/' + self.parlement_and_politiek_id + '/'

    @staticmethod
    def get_name_parts(fullname, wikidata_item):
        name_parts = fullname.split(' ')
        surname_prefix = ''
        if len(name_parts) == 2:
            forename = name_parts[0]
            surname = name_parts[1]
            return forename.strip(), surname.strip(), surname_prefix.strip()
        surname_prefix, prefix_pos = Person.find_prefix(fullname)
        if surname_prefix:
            forename = fullname[0:prefix_pos]
            surname_pos = prefix_pos + len(surname_prefix)
            surname = fullname[surname_pos:]
            return forename.strip(), surname.strip(), surname_prefix.strip()
        given_names = wikidata_item.get_given_names()
        if given_names:
            surname = fullname
            for name in given_names:
                name_pos = fullname.find(name + ' ')
                if name_pos >= 0 and (name_pos == 0 or fullname[name_pos - 1] == ' '):  # not part of a longer name
                    surname = surname.replace(name, '').strip()
            if surname != fullname:
                forename = fullname.replace(surname, '').strip()
            else:
                surname = name_parts[-1]
                forename = fullname.replace(surname, '')
            return forename.strip(), surname.strip(), surname_prefix.strip()
        else:
            surname = name_parts[-1]
            forename = fullname.replace(surname, '')
            return forename.strip(), surname.strip(), surname_prefix.strip()

    @staticmethod
    def same_surname():
        same_name_ids = []
        persons = Person.objects.all()
        for person in persons:
            persons_same_name = Person.objects.filter(surname__iexact=person.surname)
            if persons_same_name.count() > 1:
                for p in persons_same_name:
                    same_name_ids.append(p.id)
        return Person.objects.filter(pk__in=same_name_ids).order_by('surname')
