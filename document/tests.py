import datetime

from django.test import TestCase

from document.models import Document
from document.models import Dossier
from document.models import Submitter
from document.models import CategoryDossier
from document.models import CategoryDocument
from document.models import Voting
from document.models import VoteIndividual, VoteParty
from document.models import Kamervraag

from person.models import Person
from parliament.models import ParliamentMember
from parliament.models import PoliticalParty
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
        document.delete()
        submitter.delete()


class TestVoting(TestCase):
    fixtures = ['person.json', 'parliament.json']

    @classmethod
    def setUpTestData(cls):
        cls.dossier = Dossier.objects.create(dossier_id='33333', title='test dossier')
        cls.voting = Voting.objects.create(
            dossier=cls.dossier,
            is_dossier_voting=True,
            date=datetime.date(year=2016, month=6, day=1)
        )

    def test_party_voting(self):
        vote = VoteParty.objects.create(
            voting=self.voting,
            party_name='PvdA',
            number_of_seats=10
        )
        party_expected = PoliticalParty.objects.filter(name_short='PvdA')[0]
        vote.set_derived()
        self.assertEqual(vote.party, party_expected)

    def test_individual_voting(self):
        pijkstra = Person.find_surname_initials('Dijkstra', 'P.A.')
        vote = VoteIndividual.objects.create(
            voting=self.voting,
            person_name='Dijkstra, P.A.',
            person_tk_id=pijkstra.tk_id,
            number_of_seats=1
        )
        vote.set_derived()
        self.assertEqual(vote.parliament_member.person.surname, 'Dijkstra')

    def test_delete_parliament_member(self):
        member = ParliamentMember.find('Dijkstra', initials='P.A.')
        vote = VoteIndividual.objects.create(
            voting=self.voting,
            person_name='Dijkstra, P.A.',
            person_tk_id=member.person.tk_id,
            number_of_seats=1
        )
        vote.set_derived()
        self.assertEqual(member, vote.parliament_member)
        ParliamentMember.objects.all().delete()
        vote = VoteIndividual.objects.filter(id=vote.id)
        self.assertEqual(vote, vote)
