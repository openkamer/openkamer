import datetime

import requests

from django.test import TestCase

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
