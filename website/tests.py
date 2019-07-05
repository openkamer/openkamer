import datetime
import logging

from django.contrib.auth.models import User
from django.test import Client
from django.test import TestCase
from django.urls import reverse

import scraper.documents

from person.models import Person

from parliament.models import ParliamentMember
from parliament.models import PoliticalParty

from document.models import Agenda
from document.models import BesluitenLijst
from document.models import CategoryDossier
from document.models import CategoryDocument
from document.models import Dossier
from document.models import Document
from document.models import Kamerstuk
from document.models import Voting

import openkamer.besluitenlijst
import openkamer.document
import openkamer.dossier
import openkamer.kamerstuk

logger = logging.getLogger(__name__)


class TestExample(TestCase):

    def test_example(self):
        logger.info('BEGIN')
        logger.info('END')


class TestFindParliamentMembers(TestCase):
    fixtures = ['person.json', 'parliament.json']

    def test_find_member(self):
        surname = 'Zijlstra'
        forename = 'Halbe'
        initials = 'H.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_surname_prefix(self):
        surname = 'Weyenberg van'
        forename = 'Steven'
        initials = 'S.P.R.A.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
        surname = 'van Weyenberg'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)

    def test_find_member_non_ascii(self):
        surname = 'Koser Kaya'
        forename = 'Fatma'
        initials = 'F.'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)
        surname = 'Koşer Kaya'
        member = ParliamentMember.find(surname=surname, initials=initials)
        self.assertEqual(member.person.forename, forename)


class TestPersonView(TestCase):
    fixtures = ['person.json']

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()

    def test_persons_overview(self):
        response = self.client.get(reverse('persons'))
        self.assertEqual(response.status_code, 200)

    def test_person_overview(self):
        persons = Person.objects.all()[:10]
        for person in persons:
            response = self.client.get(reverse('person', args=(person.slug,)))
            self.assertEqual(response.status_code, 200)

    def test_person_check_view(self):
        response = self.client.get(reverse('persons-check'))
        self.assertEqual(response.status_code, 200)


class TestWebsite(TestCase):
    fixtures = ['person.json', 'parliament.json', 'government.json']

    @classmethod
    def setUpTestData(cls):
        # TODO: improve performance of votings (tkapi)
        openkamer.dossier.create_dossier_retry_on_error(33885)
        openkamer.dossier.create_dossier_retry_on_error(33506)
        cls.client = Client()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_persons_overview(self):
        response = self.client.get(reverse('persons'))
        self.assertEqual(response.status_code, 200)

    def test_person_overview(self):
        persons = Person.objects.all()[:10]
        for person in persons:
            response = self.client.get(reverse('person', args=(person.slug,)))
            self.assertEqual(response.status_code, 200)

    def test_person_autocomplete_view(self):
        response = self.client.get(reverse('person-autocomplete') + '?q=samsom')
        self.assertEqual(response.status_code, 200)

    def test_dossiers_overview(self):
        response = self.client.get(reverse('wetsvoorstellen'))
        self.assertEqual(response.status_code, 200)

    def test_dossiers_filter_view(self):
        ivo = Person.objects.filter(forename='Ivo', surname='Opstelten')[0]
        response = self.client.get(reverse('wetsvoorstellen') + '?title=wet&submitter=' + str(ivo.id) + '&voting_result=AAN')
        self.assertEqual(response.status_code, 200)

    def test_dossier_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-tiles', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)

    def test_timeline_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-timeline', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)

    def test_timeline_horizontal_views(self):
        dossiers = Dossier.objects.all()
        for dossier in dossiers:
            response = self.client.get(reverse('dossier-timeline-horizontal', args=(dossier.dossier_id,)))
            self.assertEqual(response.status_code, 200)
            response = self.client.get('/dossier/timeline/horizontal/json/?dossier_pk=' + str(dossier.id))
            self.assertEqual(response.status_code, 200)

    def test_document_view(self):
        documents = Document.objects.all()
        for document in documents:
            response = self.client.get(reverse('document', args=(document.document_id,)))
            self.assertEqual(response.status_code, 200)

    def test_kamerstuk_view(self):
        kamerstukken = Kamerstuk.objects.all()
        for kamerstuk in kamerstukken:
            response = self.client.get(reverse('kamerstuk', args=(kamerstuk.id_main, kamerstuk.id_sub,)))
            self.assertEqual(response.status_code, 200)

    def test_kamerstuk_modifications(self):
        kamerstuk_08 = Kamerstuk.objects.get(id_main='33885', id_sub='8')
        kamerstuk_11 = Kamerstuk.objects.get(id_main='33885', id_sub='11')
        kamerstuk_29 = Kamerstuk.objects.get(id_main='33885', id_sub='29')
        kamerstuk_original = Kamerstuk.objects.get(id_main='33885', id_sub='2')
        self.assertEqual(kamerstuk_08.original, kamerstuk_original)
        self.assertEqual(kamerstuk_11.original, kamerstuk_original)
        self.assertEqual(kamerstuk_29.original, kamerstuk_original)
        modifications = [kamerstuk_08, kamerstuk_11, kamerstuk_29]
        for modification in kamerstuk_original.modifications:
            self.assertTrue(modification in modifications)

    def test_agendas_view(self):
        response = self.client.get('/agendas/')
        self.assertEqual(response.status_code, 200)

    def test_agenda_view(self):
        agendas = Agenda.objects.all()
        for agenda in agendas:
            response = self.client.get('/agenda/' + str(agenda.agenda_id) + '/')
            self.assertEqual(response.status_code, 200)

    def test_votings_overview(self):
        response = self.client.get(reverse('votings'))
        self.assertEqual(response.status_code, 200)

    def test_voting_view(self):
        votings = Voting.objects.all()
        for voting in votings:
            if voting.is_dossier_voting:
                response = self.client.get(reverse('voting-dossier', args=(voting.dossier.dossier_id,)))
            elif voting.kamerstuk:
                response = self.client.get(reverse('voting-kamerstuk', args=(voting.kamerstuk.id_main, voting.kamerstuk.id_sub,)))
            else:
                print('WARNING: no kamerstuk found for voting id: {}'.format(voting.id))
                continue
            self.assertEqual(response.status_code, 200)

    def test_parties_overview(self):
        response = self.client.get(reverse('parties'))
        self.assertEqual(response.status_code, 200)

    def test_party_view(self):
        parties = PoliticalParty.objects.all()
        for party in parties:
            if not party.slug:
                print('WARNING: Empty party found, skipping view')
                continue
            response = self.client.get(reverse('party', args=(party.slug,)))
            self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(parties), 60)

    def test_besluitenlijsten_view(self):
        response = self.client.get(reverse('besluitenlijsten'))
        self.assertEqual(response.status_code, 200)

    def test_besluitenlijst_view(self):
        lijsten = BesluitenLijst.objects.all()
        for lijst in lijsten:
            response = self.client.get(reverse('besluitenlijst', args=(lijst.activity_id,)))
            self.assertEqual(response.status_code, 200)

    def test_parliament_members_overview(self):
        response = self.client.get(reverse('parliament-members'))
        self.assertEqual(response.status_code, 200)

    def test_parliament_members_check(self):
        password = 'adminpassword'
        my_admin = User.objects.create_superuser('adminuser', 'admin@admin.com', password)
        self.client.login(username=my_admin.username, password=password)
        response = self.client.get(reverse('parliament-members-check'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_database_dumps_view(self):
        response = self.client.get(reverse('database-dumps'))
        self.assertEqual(response.status_code, 200)

    def test_stats_view(self):
        response = self.client.get(reverse('stats'))
        self.assertEqual(response.status_code, 200)

    def test_data_stats_view(self):
        response = self.client.get(reverse('stats-data'))
        self.assertEqual(response.status_code, 200)

    def test_plot_example_view(self):
        response = self.client.get('/stats/exampleplots/')
        self.assertEqual(response.status_code, 200)

    def test_api_homepage(self):
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)

    def test_api_person(self):
        response = self.client.get('/api/person/')
        self.assertEqual(response.status_code, 200)

    def test_api_parliament(self):
        response = self.client.get('/api/parliament/')
        self.assertEqual(response.status_code, 200)

    def test_api_parliament_member(self):
        response = self.client.get('/api/parliament_member/')
        self.assertEqual(response.status_code, 200)

    def test_api_party(self):
        response = self.client.get('/api/party/')
        self.assertEqual(response.status_code, 200)

    def test_api_party_member(self):
        response = self.client.get('/api/party_member/')
        self.assertEqual(response.status_code, 200)

    def test_api_document(self):
        response = self.client.get('/api/document/')
        self.assertEqual(response.status_code, 200)

    def test_api_kamerstuk(self):
        response = self.client.get('/api/kamerstuk/')
        self.assertEqual(response.status_code, 200)

    def test_api_submitter(self):
        response = self.client.get('/api/submitter/')
        self.assertEqual(response.status_code, 200)

    def test_api_dossier(self):
        response = self.client.get('/api/dossier/')
        self.assertEqual(response.status_code, 200)

    def test_api_voting(self):
        response = self.client.get('/api/voting/')
        self.assertEqual(response.status_code, 200)

    def test_api_voteparty(self):
        response = self.client.get('/api/vote_party/')
        self.assertEqual(response.status_code, 200)

    def test_api_voteindividual(self):
        response = self.client.get('/api/vote_individual/')
        self.assertEqual(response.status_code, 200)

    def test_api_category_dossier(self):
        response = self.client.get('/api/category_dossier/')
        self.assertEqual(response.status_code, 200)

    def test_api_category_document(self):
        response = self.client.get('/api/category_document/')
        self.assertEqual(response.status_code, 200)


class TestCategory(TestCase):

    def test_create_dossier_category_from_string(self):
        self.create_category_from_string(CategoryDossier)

    def test_create_document_category_from_string(self):
        self.create_category_from_string(CategoryDocument)

    def create_category_from_string(self, category_class):
        text = 'Zorg en gezondheid | Ziekten en behandelingen'
        expected_names = [
            'zorg en gezondheid',
            'ziekten en behandelingen',
        ]
        categories = openkamer.dossier.get_categories(text, category_class)
        self.assertEqual(len(categories), 2)
        for index, category in enumerate(categories):
            self.assertEqual(expected_names[index], category.name)
        text = '  Zorg en Gezondheid|  Ziekten en Behandelingen'
        expected_names = [
            'zorg en gezondheid',
            'ziekten en behandelingen',
        ]
        categories = openkamer.dossier.get_categories(text, category_class)
        self.assertEqual(len(categories), 2)
        for index, category in enumerate(categories):
            self.assertEqual(expected_names[index], category.name)


class TestDocumentLinks(TestCase):

    @classmethod
    def setUpTestData(cls):
        dosser_id = '33569'
        dossier = Dossier.objects.create(dossier_id=dosser_id)
        document = Document.objects.create(dossier=dossier)
        Kamerstuk.objects.create(document=document, id_main=dosser_id, id_sub='1')
        Kamerstuk.objects.create(document=document, id_main=dosser_id, id_sub='2')
        Kamerstuk.objects.create(document=document, id_main=dosser_id, id_sub='3')

    def test_create_new_url(self):
        url = 'kst-33569-1.html'
        url_expected = '/kamerstuk/33569/1/'
        self.check_url(url, url_expected)
        url = 'kst-33569-A.html'
        url_expected = 'https://zoek.officielebekendmakingen.nl/kst-33569-A.html'
        self.check_url(url, url_expected)
        url = 'http://www.google.com'
        url_expected = 'http://www.google.com'
        self.check_url(url, url_expected)
        url = '#anchor-1'
        url_expected = '#anchor-1'
        self.check_url(url, url_expected)

    def check_url(self, url, url_expected):
        new_url = openkamer.document.create_new_url(url)
        self.assertEqual(new_url, url_expected)
        url = new_url
        new_url = openkamer.document.create_new_url(url)
        self.assertEqual(new_url, url)
