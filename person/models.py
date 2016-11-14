import logging
from unidecode import unidecode

from django.db import models
from django.utils.text import slugify

from wikidata import wikidata

logger = logging.getLogger(__name__)


NAME_PREFIXES = [
    'van der',
    'van den',
    'van de',
    'van \'t',
    'in het',
    'van',
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
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, default='')
    initials = models.CharField(max_length=200, blank=True, default='')
    birthdate = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
    wikipedia_url = models.URLField(blank=True)
    wikimedia_image_name = models.CharField(max_length=200, blank=True)
    wikimedia_image_url = models.URLField(blank=True)
    parlement_and_politiek_id = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=250, default='')

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
        for prefix in NAME_PREFIXES:
            prefix_pos = name.find(prefix + ' ')
            if prefix_pos >= 0 and (prefix_pos == 0 or name[prefix_pos-1] == ' '):  # prefix must be at the start or there should be a whitespace in front
                name_prefix = prefix
                return name_prefix, prefix_pos
        return '', -1

    @staticmethod
    def find_surname_initials(surname, initials=''):
        logger.info('surname: ' + surname + ', initials: ' + initials)
        surname = unidecode(surname)
        initials = unidecode(initials)
        persons = Person.objects.all()
        best_match = None
        best_score = 0
        for person in persons:
            score = 0
            if surname.lower() == unidecode(person.surname.lower()):
                score += 1
            elif surname.lower() == unidecode(person.surname.lower() + ' ' + person.surname_prefix.lower()):
                score += 1
            elif surname.lower() == unidecode(person.surname_prefix.lower() + ' ' + person.surname.lower()):
                score += 1
            intials_letters = initials.split('.')
            forename = unidecode(person.forename)
            if initials.lower() == unidecode(person.initials.lower()):
                score += 1
            elif intials_letters and forename and intials_letters[0] == forename[0]:
                score += 0.5
            if score >= 1.5 and score > best_score:
                best_match = person
                best_score = score
        if best_match:
            logger.info('person found: ' + surname + ', ' + initials + ' : ' + str(best_match))
        return best_match

    @staticmethod
    def find_by_fullname(fullname):
        persons = Person.objects.all()
        for person in persons:
            if person.fullname() == fullname:
                return person
        return None

    def fullname(self):
        return self.get_full_name()

    def get_full_name(self):
        fullname = self.forename
        fullname += ' ' + self.surname_including_prefix()
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
        persons = Person.objects.all()
        for person in persons:
            person.update_info(language=language)
            person.save()

    def find_wikidata_id(self, language='en'):
        wikidata_id = wikidata.search_wikidata_id(self.get_full_name(), language)
        logger.info('wikidata id: ' + str(wikidata_id))
        return wikidata_id

    def update_info(self, language='en', wikidata_item=None):
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

