from datetime import date

import requests

from django.test import TestCase

from person.models import Person


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
        self.assertEqual(person.birthdate, date(1967, 2, 14))
