import datetime

import requests

from django.test import TestCase

from wikidata import wikidata
from person.models import Person


class TestFindName(TestCase):

    def test_find_by_fullname(self):
        p1 = Person.objects.create(forename='Jan Peter', surname='Balkenende', initials='J.P.')
        p2 = Person.objects.create(forename='Jan', surname='Balkenende', initials='J.')
        p3 = Person.objects.create(forename='Jan', surname='Balkenende', surname_prefix='van', initials='J.')
        p4 = Person.objects.create(forename='Jan Peter', surname='Balkenende', surname_prefix='van', initials='J.P.')
        p_found = Person.find_by_fullname('Jan Peter Balkenende')
        self.assertEqual(p1.id, p_found.id)
        p_found = Person.find_by_fullname('Jan Balkenende')
        self.assertEqual(p2.id, p_found.id)
        p_found = Person.find_by_fullname('Jan van Balkenende')
        self.assertEqual(p3.id, p_found.id)
        p_found = Person.find_by_fullname('Jan Peter van Balkenende')
        self.assertEqual(p4.id, p_found.id)
        p_found = Person.find_by_fullname('Jan Jaap van Balkenende')
        self.assertEqual(None, p_found)


class TestNamePrefix(TestCase):

    def test_find_name_prefix(self):
        name = 'Ard van der Steur'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'Ard van derSteur'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')
        name = 'Ard van de Steur'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van de')
        name = 'Ard van Steur'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')
        name = 'Gerard \'t Hooft'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, '\'t')
        name = 'Jan Peter Balkenende'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, '')
        name = 'Boris van der Ham'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'van der Ham'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'van derHam'
        prefix = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')


class TestCreatePerson(TestCase):

    def test_create_person(self):
        forename = 'Mark'
        surname = 'Rutte'
        person = Person.objects.create(forename=forename, surname=surname)
        self.assertEqual(Person.objects.count(), 1)
        self.assertTrue(Person.person_exists(forename, surname))
        person.update_info()
        person.save()
        self.assertEqual(person.wikidata_id, 'Q57792')
        self.assertEqual(person.wikimedia_image_name.split('.')[1], 'jpg')
        response = requests.get(person.wikimedia_image_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(person.birthdate, datetime.date(1967, 2, 14))
        self.assertEqual(person.slug, 'mark-rutte')


class TestWikidataNameParts(TestCase):

    def test_fatma_koser_kaya(self):
        wikidata_id = 'Q467610'  # Fatma Koşer Kaya
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Fatma')
        self.assertEqual(surname, 'Koşer Kaya')
        self.assertEqual(surname_prefix, '')

    def test_jan_peter_balkenende(self):
        wikidata_id = 'Q133386'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Jan Peter')
        self.assertEqual(surname, 'Balkenende')
        self.assertEqual(surname_prefix, '')

    def test_jan_kees_de_jager(self):
        wikidata_id = 'Q1666631'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Jan Kees')
        self.assertEqual(surname, 'Jager')
        self.assertEqual(surname_prefix, 'de')

    def test_sjoerd_sjoerdsma(self):
        wikidata_id = 'Q516335'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Sjoerd')
        self.assertEqual(surname, 'Sjoerdsma')
        self.assertEqual(surname_prefix, '')

    def test_sybrand_van_haersma_buma(self):
        wikidata_id = 'Q377266'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Sybrand')
        self.assertEqual(surname, 'Haersma Buma')
        self.assertEqual(surname_prefix, 'van')

    def test_chantal_nijkerken_de_haan(self):
        wikidata_id = 'Q19830701'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Chantal')
        self.assertEqual(surname, 'Nijkerken-de Haan')
