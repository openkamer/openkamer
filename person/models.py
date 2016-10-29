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
    'in het',
    'van',
    'de',
    'het',
    '\'t',
    'der',
    'ter',
    'te',
]


class Person(models.Model):
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    surname_prefix = models.CharField(max_length=200, blank=True, default='')
    initials = models.CharField(max_length=200, blank=True, default='')
    birthdate = models.DateField(blank=True, null=True)
    wikidata_id = models.CharField(max_length=200, blank=True)
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
        name_prefix = ''
        for prefix in NAME_PREFIXES:
            if prefix + ' ' in name:
                name_prefix = prefix
                break
        return name_prefix

    @staticmethod
    def find(surname, initials=''):
        logger.info('surname: ' + surname + ', initials: ' + initials)
        surname = unidecode(surname)
        initials = unidecode(initials)
        persons = Person.objects.all()
        for person in persons:
            score = 0
            if surname.lower() == unidecode(person.surname.lower()):
                score += 1
            if surname.lower() == unidecode(person.surname.lower() + ' ' + person.surname_prefix.lower()):
                score += 1
            if surname.lower() == unidecode(person.surname_prefix.lower() + ' ' + person.surname.lower()):
                score += 1
            if initials.lower() == unidecode(person.initials.lower()):
                score += 1
            if score >= 2:
                logger.info('person found: ' + surname + ', ' + initials + ' : ' + str(person))
                return person
        return None

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
        if self.surname_prefix:
            fullname += ' ' + str(self.surname_prefix)
        fullname += ' ' + str(self.surname)
        return fullname

    @staticmethod
    def person_exists(forename, surname):
        return Person.objects.filter(forename=forename, surname=surname).exists()

    @staticmethod
    def update_persons_all(language):
        persons = Person.objects.all()
        for person in persons:
            person.update_info(language=language)
            person.save()

    def update_info(self, language='en'):
        logger.info('get info from wikidata for ' + self.get_full_name())
        wikidata_id = wikidata.search_wikidata_id(self.get_full_name(), language)
        if not wikidata_id:
            return
        logger.info('wikidata id: ' + wikidata_id)
        self.wikidata_id = wikidata_id
        birthdate = wikidata.get_birth_date(self.wikidata_id)
        if birthdate:
            self.birthdate = birthdate
        image_filename = wikidata.get_image_filename(self.wikidata_id)
        if image_filename:
            self.wikimedia_image_name = image_filename
            self.wikimedia_image_url = wikidata.get_wikimedia_image_url(self.wikimedia_image_name)
        self.parlement_and_politiek_id = wikidata.get_parlement_and_politiek_id(self.wikidata_id)

    def get_wikidata_url(self):
        return 'https://www.wikidata.org/wiki/Special:EntityData/' + str(self.wikidata_id)

    def parlement_and_politiek_url(self):
        return 'https://www.parlement.com/id/' + self.parlement_and_politiek_id + '/'
