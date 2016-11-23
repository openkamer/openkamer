import datetime

from django.test import TestCase

from document.models import Document
from document.models import Dossier
from document.models import Submitter
from document.models import CategoryDossier
from document.models import CategoryDocument

from person.models import Person
from government.models import Government
from government.models import Ministry
from government.models import GovernmentMember
from government.models import GovernmentPosition


class TestExample(TestCase):
    """ Example test case """

    def test_example(self):
        """ Example test """
        self.assertEqual(1, 1)
        self.assertTrue(True)
        self.assertFalse(False)


class TestCategory(TestCase):

    def test_create_dossier_category(self):
        category, created = CategoryDossier.objects.get_or_create(name='Test Category Name')
        self.assertEqual(category.slug, 'test-category-name')

    def test_create_document_category(self):
        category, created = CategoryDocument.objects.get_or_create(name='Test Category Name')
        self.assertEqual(category.slug, 'test-category-name')


class TestSubmitter(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.government = Government.objects.create(name='Kabinet-Rutte II', date_formed=datetime.date(2012, 11, 5))
        cls.ministry = Ministry.objects.create(name='Veiligheid en Justitie', government=cls.government)
        cls.person = Person.objects.create(surname='Blok', forename='Stef')
        gov_pos_minister = GovernmentPosition.objects.create(
            position=GovernmentPosition.MINISTER,
            ministry=cls.ministry,
            government=cls.government
        )
        cls.gov_member1 = GovernmentMember.objects.create(
            person=cls.person,
            position=gov_pos_minister,
            start_date=datetime.date(2015, 3, 10),
            end_date=datetime.date(2015, 3, 20)
        )
        gov_pos_mwop = GovernmentPosition.objects.create(
            position=GovernmentPosition.MINISTER_WO_PORTFOLIO,
            government=cls.government,
            extra_info='Wonen en Rijksdienst'
        )
        cls.gov_member2 = GovernmentMember.objects.create(
            person=cls.person,
            position=gov_pos_mwop,
            start_date=datetime.date(2012, 11, 5)
        )
        gov_pos_ss = GovernmentPosition.objects.create(
            position=GovernmentPosition.SECRETARY_OF_STATE,
            ministry=cls.ministry,
            government=cls.government,
            extra_info='Wonen en Rijksdienst'
        )
        cls.gov_member3 = GovernmentMember.objects.create(
            person=cls.person,
            position=gov_pos_ss,
            start_date=datetime.date(2015, 3, 20),
            end_date=datetime.date(2016, 3, 20)
        )

    def test_get_government_member(self):
        self.check_document_goverment_member(datetime.date(2015, 3, 10), [self.gov_member1, self.gov_member2])
        self.check_document_goverment_member(datetime.date(2012, 12, 25), [self.gov_member2])
        self.check_document_goverment_member(datetime.date(2015, 6, 22), [self.gov_member2, self.gov_member3])

    def check_document_goverment_member(self, document_date, expected_members):
        document = Document.objects.create(date_published=document_date)
        submitter = Submitter.objects.create(person=self.person, document=document)
        members = submitter.government_members
        self.assertEqual(len(members), len(expected_members))
        for mem in members:
            self.assertTrue(mem in expected_members)


class TestDossier(TestCase):

    def test_get_active_ids(self):
        active_ids = Dossier.get_active_dossier_ids()
        active_ids_cached = Dossier.get_active_dossier_ids()
        self.assertEqual(len(active_ids), len(active_ids_cached))

    def test_get_inactive_ids(self):
        inactive_ids = Dossier.get_inactive_dossier_ids()
        inactive_ids_cached = Dossier.get_inactive_dossier_ids()
        self.assertEqual(len(inactive_ids), len(inactive_ids_cached))
