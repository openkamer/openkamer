import datetime

import requests

from django.test import TestCase

from wikidata import wikidata
from person.models import Person
from person.util import parse_name_surname_initials, parse_surname_comma_surname_prefix


class TestFindName(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.p1 = Person.objects.create(forename='Jan Peter', surname='Balkenende', initials='J.P.')
        cls.p2 = Person.objects.create(forename='Jan', surname='Balkenende', initials='J.')
        cls.p3 = Person.objects.create(forename='Jan', surname='Balkenende', surname_prefix='van', initials='J.')
        cls.p4 = Person.objects.create(forename='Jan Peter', surname='Balkenende', surname_prefix='van', initials='J.P.')
        cls.p5 = Person.objects.create(forename='Fatma', surname='Koşer Kaya', surname_prefix='', initials='F.')
        cls.p6 = Person.objects.create(forename='Jan Peter', surname='Balkenende', initials='')
        cls.p7 = Person.objects.create(forename='', surname='van Raak', initials='')
        cls.p8 = Person.objects.create(forename='', surname='Grapperhaus', initials='F.B.J.')
        cls.p9 = Person.objects.create(forename='Ferdinand', surname='Grapperhaus', initials='F.B.J.')

    def test_find_by_fullname(self):
        p_found = Person.find_by_fullname('Jan Peter Balkenende')
        self.assertEqual(self.p1, p_found)
        p_found = Person.find_by_fullname('Jan Balkenende')
        self.assertEqual(self.p2, p_found)
        p_found = Person.find_by_fullname('Jan van Balkenende')
        self.assertEqual(self.p3, p_found)
        p_found = Person.find_by_fullname('Jan Peter van Balkenende')
        self.assertEqual(self.p4, p_found)
        p_found = Person.find_by_fullname('Jan Jaap van Balkenende')
        self.assertEqual(None, p_found)
        p_found = Person.find_by_fullname('van Raak')
        self.assertEqual(self.p7, p_found)

    def test_find_by_surname_initials(self):
        p_found = Person.find_surname_initials('Balkenende', 'J.P.')
        self.assertEqual(p_found, self.p1)
        p_found = Person.find_surname_initials('Balkenende', 'J.')
        self.assertEqual(p_found, self.p2)
        p_found = Person.find_surname_initials('Balkenende', '')
        self.assertEqual(p_found, None)
        p_found = Person.find_surname_initials('van der Steur', 'J.P.')
        self.assertEqual(p_found, None)
        p_found = Person.find_surname_initials('Koşer Kaya', 'F.')
        self.assertEqual(p_found, self.p5)

    def test_find_surname_multiple(self):
        p_found = Person.find_surname_initials('Grapperhaus', 'F.B.J.')
        self.assertEqual(p_found, self.p9)


class TestNamePrefix(TestCase):

    def test_find_name_prefix(self):
        name = 'Ard van der Steur'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'Ard van derSteur'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')
        name = 'Ard van de Steur'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van de')
        name = 'Ard van Steur'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')
        name = 'Gerard \'t Hooft'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, '\'t')
        name = 'Jan Peter Balkenende'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, '')
        name = 'Boris van der Ham'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'van der Ham'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van der')
        name = 'van derHam'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'van')
        name = 'von Martels'
        prefix, pos = Person.find_prefix(name)
        self.assertEqual(prefix, 'von')

    def test_parse_surname_surname_prefix(self):
        surname_expected = 'Ham'
        surname_prefix_expected = 'van der'
        surname, surname_prefix = parse_surname_comma_surname_prefix('Ham, van der')
        self.assertEqual(surname, surname_expected)
        self.assertEqual(surname_prefix, surname_prefix_expected)


class TestCreatePerson(TestCase):

    def test_create_person(self):
        forename = 'Mark'
        surname = 'Rutte'
        person = Person.objects.create(forename=forename, surname=surname)
        self.assertEqual(Person.objects.count(), 1)
        self.assertTrue(Person.person_exists(forename, surname))
        person.update_info(language='nl')
        person.save()
        self.assertEqual(person.wikidata_id, 'Q57792')
        self.assertEqual(person.wikimedia_image_name.split('.')[1], 'jpg')
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

    def test_leendert_de_lange(self):
        wikidata_id = 'Q19839084'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Leendert')
        self.assertEqual(surname_prefix, 'de')
        self.assertEqual(surname, 'Lange')

    def test_melanie_schultz_van_hagen(self):
        wikidata_id = 'Q435886'
        wikidata_item = wikidata.WikidataItem(wikidata_id)
        fullname = wikidata_item.get_label()
        forename, surname, surname_prefix = Person.get_name_parts(fullname, wikidata_item)
        self.assertEqual(forename, 'Melanie')
        self.assertEqual(surname_prefix, '')
        self.assertEqual(surname, 'Maas Geesteranus')


class TestParseName(TestCase):
    """ Tests name parsing """
    initials_expected = 'P.A.'
    surname_expected = 'Dijkstra'

    def check_result(self, initials, surname):
        self.assertEqual(initials, self.initials_expected)
        self.assertEqual(surname, self.surname_expected)

    def test_initials_surname(self):
        name = 'P.A. Dijkstra'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)

    def test_initials_surname_forname(self):
        name = 'P.A. (Pia) Dijkstra'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'P.A. (Pia)Dijkstra'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)

    def test_surname_initials(self):
        name = 'Dijkstra, P.A.'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra,P.A.'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra P.A.'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra P.A. (Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra, (Pia) P.A.'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)

    def test_surname_initials_forname(self):
        name = 'Dijkstra, P.A.(Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra, P.A. (Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)
        name = 'Dijkstra,P.A.(Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.check_result(initials, surname)

    def test_surname_prefix(self):
        name = 'van Dijkstra, P.A.(Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.assertEqual(surname_prefix, 'van')
        self.check_result(initials, surname)
        name = 'Dijkstra van, P.A. (Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.assertEqual(surname_prefix, 'van')
        self.check_result(initials, surname)
        name = 'van Dijkstra,P.A.(Pia)'
        initials, surname, surname_prefix = parse_name_surname_initials(name)
        self.assertEqual(surname_prefix, 'van')
        self.check_result(initials, surname)

    # TODO BR: fix and enable
    # def test_initials_multicharacter(self):
    #     name = 'A.Th.B. Bijleveld-Schouten'
    #     initials, surname, surname_prefix = parse_name_surname_initials(name)
    #     self.assertEqual(initials, 'A.Th.B.')
