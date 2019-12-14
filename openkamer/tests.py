import datetime

from django.urls import reverse
from django.test import TestCase

from tkapi import TKApi
from tkapi.besluit import Besluit as TKBesluit
from tkapi.document import DocumentSoort
from tkapi.document import Document as TKDocument
from tkapi.util import queries
from tkapi.util.document import get_overheidnl_id
from tkapi.zaak import Zaak

from person.models import Person

from government.models import Government

from parliament.models import Parliament
from parliament.models import PartyMember
from parliament.models import PoliticalParty
from parliament.models import Commissie

from document.models import Document
from document.models import Dossier
from document.models import Kamervraag
from document.models import Voting, Vote

from openkamer.document import DocumentFactory
import openkamer.dossier
import openkamer.kamerstuk
import openkamer.kamervraag
import openkamer.parliament
import openkamer.voting
import openkamer.gift
import openkamer.verslagao


class TestCreatePerson(TestCase):
    wikidata_id_ss = 'Q516335'
    name_ss = 'Sjoerd Sjoerdsma'

    def test_create_person_from_wikidata_id(self):
        person = openkamer.parliament.get_or_create_person(self.wikidata_id_ss, add_initials=True)
        self.check_sjoerd(person)

    def test_create_person_from_wikidata_id_and_fullname(self):
        person = openkamer.parliament.get_or_create_person(self.wikidata_id_ss, self.name_ss, add_initials=True)
        self.check_sjoerd(person)

    def check_sjoerd(self, person):
        self.assertTrue('Sjoerdsma' in person.surname)
        self.assertEqual(person.forename, 'Sjoerd')
        self.assertEqual(person.surname, 'Sjoerdsma')
        self.assertEqual(person.initials, 'S.W.')

    def test_jeroen_wikidata(self):
        wikidata_id = 'Q17428405'
        person = openkamer.parliament.get_or_create_person(wikidata_id)
        self.assertEqual(person.forename, 'Jeroen')
        self.assertEqual(person.surname_prefix, 'van')
        self.assertEqual(person.surname, 'Wijngaarden')
        self.assertEqual(person.fullname(), 'Jeroen van Wijngaarden')

    def test_jan_kees_wikidata(self):
        wikidata_id = 'Q1666631'
        person = openkamer.parliament.get_or_create_person(wikidata_id)
        self.assertEqual(person.forename, 'Jan Kees')
        self.assertEqual(person.surname_prefix, 'de')
        self.assertEqual(person.surname, 'Jager')
        self.assertEqual(person.fullname(), 'Jan Kees de Jager')

    def test_eelke_wikidata(self):
        wikidata_id = 'Q2710877'
        person = openkamer.parliament.get_or_create_person(wikidata_id)
        self.assertEqual(person.forename, 'Eeke')
        self.assertEqual(person.surname_prefix, 'van der')
        self.assertEqual(person.surname, 'Veen')
        self.assertEqual(person.fullname(), 'Eeke van der Veen')

    def test_koser_kaya_wikidata(self):
        wikidata_id = 'Q467610'
        person = openkamer.parliament.get_or_create_person(wikidata_id)
        self.assertEqual(person.forename, 'Fatma')
        self.assertEqual(person.surname_prefix, '')
        self.assertEqual(person.surname, 'Koşer Kaya')
        self.assertEqual(person.fullname(), 'Fatma Koşer Kaya')


class TestFindOriginalKamerstukId(TestCase):
    dossier_id = 33885

    def test_find_original_motie(self):
        expected_result = '33885-18'
        title = 'Gewijzigde motie van het lid Segers c.s. (t.v.v. 33885, nr.18) over de bevoegdheden van de Koninklijke Marechaussee'
        original_id = openkamer.kamerstuk.find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_amendement(self):
        title = 'Gewijzigd amendement van het lid Oskam ter vervanging van nr. 9 waarmee een verbod op illegaal pooierschap in het wetboek van strafrecht wordt geintroduceerd'
        expected_result = '33885-9'
        original_id = openkamer.kamerstuk.find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_voorstel_van_wet(self):
        title = 'Wijziging van de Wet regulering prostitutie en bestrijding misstanden seksbranche; Gewijzigd voorstel van wet '
        expected_result = '33885-voorstel_van_wet'
        original_id = openkamer.kamerstuk.find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_none(self):
        title = 'Motie van de leden Volp en Kooiman over monitoring van het nulbeleid'
        expected_result = ''
        original_id = openkamer.kamerstuk.find_original_kamerstuk_id(self.dossier_id, title)
        self.assertEqual(original_id, expected_result)

    def test_find_original_begroting_motie(self):
        title = 'Gewijzigde motie van de leden ... signaleren (t.v.v. 35300-XVI-108)'
        dossier_id = '35300-XVI'
        expected_result = '35300-XVI-108'
        original_id = openkamer.kamerstuk.find_original_kamerstuk_id(dossier_id, title)
        self.assertEqual(original_id, expected_result)


class TestCreateParliamentMember(TestCase):

    def test_create_martin(self):
        person_wikidata_id = 'Q2801440'  # Martin van Rooijen
        parliament = Parliament.get_or_create_tweede_kamer()
        members = openkamer.parliament.create_parliament_member_from_wikidata_id(parliament, person_wikidata_id)
        self.assertEqual(len(members), 1)
        party_expected = PoliticalParty.find_party('50plus')
        self.assertEqual(members[0].party, party_expected)

    def test_create_paul(self):
        person_wikidata_id = 'Q18169519'  # Paul Smeulders
        Person.objects.create(
            forename='Paul',
            surname='Smeulders',
            wikidata_id=person_wikidata_id
        )
        parliament = Parliament.get_or_create_tweede_kamer()
        members = openkamer.parliament.create_parliament_member_from_wikidata_id(parliament, person_wikidata_id)
        self.assertEqual(len(members), 1)
        member = members[0]
        party_expected = PoliticalParty.find_party('GroenLinks')
        self.assertEqual(member.party, party_expected)
        self.assertEqual(member.person.initials, '')
        member.person.update_info()
        self.assertEqual(member.person.initials, 'P.H.M.')

    def test_create_kuzu(self):
        person_wikidata_id = 'Q616635'  # Tunahan Kuzu
        parliament = Parliament.get_or_create_tweede_kamer()
        members = openkamer.parliament.create_parliament_member_from_wikidata_id(parliament, person_wikidata_id)
        self.assertEqual(len(members), 3)
        party_expected_0 = PoliticalParty.find_party('PvdA')
        party_expected_1 = PoliticalParty.find_party('GrKÖ')
        party_expected_2 = PoliticalParty.find_party('DENK')
        self.assertEqual(members[0].party, party_expected_0)
        self.assertEqual(members[1].party, party_expected_1)
        self.assertEqual(members[2].party, party_expected_2)


class TestCreatePoliticalParty(TestCase):

    def test_create_parties(self):
        parties = openkamer.parliament.create_parties(active_only=True)
        self.assertGreater(len(parties), 10)

    def test_create_socialist_party(self):
        party = openkamer.parliament.create_party('Socialistische Partij', 'SP')
        self.assertEqual(party.wikidata_id, 'Q849580')

    def test_create_party_wikidata_id(self):
        wikidata_id = 'Q849580'  # SP
        party = openkamer.parliament.create_party_wikidata(wikidata_id)
        self.assertEqual(party.name, 'Socialistische Partij')
        self.assertEqual(party.name_short, 'SP')
        self.assertEqual(party.founded, datetime.date(year=1971, month=10, day=22))
        self.assertEqual(party.slug, 'sp')


class TestCreateGovernment(TestCase):
    fixtures = ['person.json', 'parliament.json']

    @classmethod
    def setUpTestData(cls):
        rutte_2_wikidata_id = 'Q1638648'
        government = openkamer.parliament.create_government(rutte_2_wikidata_id, max_members=4)

    def test_government_data(self):
        government = Government.objects.all()[0]
        self.assertEqual(government.name, 'Kabinet-Rutte II')
        members = government.members
        persons = []
        for member in members:
            persons.append(member.person)
        party_members = PartyMember.objects.filter(person__in=persons)
        self.assertTrue(len(party_members) >= len(persons))

    def test_governements_view(self):
        response = self.client.get(reverse('governments'))
        self.assertEqual(response.status_code, 200)

    def test_governement_view(self):
        governments = Government.objects.all()
        for government in governments:
            response = self.client.get(reverse('government', args=(government.slug,)))
            self.assertEqual(response.status_code, 200)

    def test_governement_current_view(self):
        governments = Government.objects.all()
        response = self.client.get(reverse('government-current'))
        self.assertEqual(response.status_code, 200)

    def test_api_governement(self):
        response = self.client.get('/api/government/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/ministry/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/government_member/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/government_position/')
        self.assertEqual(response.status_code, 200)


class TestKamervraag(TestCase):

    def test_create_kamervraag(self):
        year = 2016
        begin_datetime = datetime.datetime(year=year, month=1, day=1)
        end_datetime = datetime.datetime(year=year, month=2, day=1)
        tk_zaken = openkamer.kamervraag.get_tk_kamervraag_zaken(begin_datetime, end_datetime)
        tk_zaak = tk_zaken[0]
        kamervraag = None
        for tk_doc in tk_zaak.documenten:
            if tk_doc.soort != DocumentSoort.SCHRIFTELIJKE_VRAGEN:
                continue
            overheid_id = get_overheidnl_id(tk_doc)
            document_factory = DocumentFactory()
            kamervraag, vraagnummer = document_factory.create_kamervraag_document(tk_doc, overheid_id)
        self.assertIsNotNone(kamervraag)

    def test_get_receiver_from_title(self):
        receiver_expected = 'Staatssecretaris van Infrastructuur en Milieu'
        title = "Vragen van het lid Monasch (PvdA) aan de Staatssecretaris van Infrastructuur en Milieu over het artikel «Schiphol kan verder met uitbreiding» (ingezonden 23 november 2015)."
        receiver = openkamer.kamervraag.get_receiver_from_title(title)
        self.assertEqual(receiver, receiver_expected)

    def test_parse_footnotes(self):
        footnote_html = """
        <div id="noten">
            <hr />
            <div class="voet noot snp-mouseoffset snb-pinned notedefault" id="supernote-note-ID-2016Z00047-d37e61">
               <h5 class="note-close"><a class="note-close" href="#close-ID-2016Z00047-d37e61">X</a> Noot
               </h5><sup><span class="nootnum"><a id="ID-2016Z00047-d37e61" name="ID-2016Z00047-d37e61"></a>1</span></sup><p><a href="http://nos.nl/l/2077649" title="link naar http://nos.nl/l/2077649" class="externe_link">http://nos.nl/l/2077649</a></p>
            </div>
            <div class="voet noot snp-mouseoffset snb-pinned notedefault" id="supernote-note-ID-2016Z00047-d37e69">
               <h5 class="note-close"><a class="note-close" href="#close-ID-2016Z00047-d37e69">X</a> Noot
               </h5><sup><span class="nootnum"><a id="ID-2016Z00047-d37e69" name="ID-2016Z00047-d37e69"></a>2</span></sup><p>VOG: verklaring omtrent gedrag</p>
            </div>
        </div>
        """
        footnotes = openkamer.kamervraag.create_footnotes(footnote_html)

    def test_find_question_in_html(self):
        document = Document.objects.create(content_html="""<div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e43" name="d16e43"></a>Vraag 1
            </h2>
            <p>Wat is uw reactie op het bericht «Veel beginnende ggz-krachten krijgen alleen onkostenvergoeding»?<a class="nootnum supernote-click-ID-2016Z00020-d37e57" href="#ID-2016Z00020-d37e57">1</a> <a class="nootnum supernote-click-n2" href="#n2">2</a></p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e55" name="d16e55"></a>Vraag 2
            </h2>
            <p>Bent u van mening dat hier sprake is van een arbeidsrelatie waarbij loon verschuldigd
               is? Zo ja, wat gaat u hieraan doen? Zo nee, waarom niet?
            </p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e62" name="d16e62"></a>Vraag 3
            </h2>
            <p>Bent u van mening dat, indien er geen sprake is van een boventallige functie waarbij
               een leerdoel centraal staat, er met terugwerkende kracht voldaan moet worden aan het
               wettelijk minimumloon dan wel de van toepassing zijnde cao? Zo ja, wat gaat u hieraan
               doen? Zo nee, waarom niet?
            </p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e69" name="d16e69"></a>Vraag 4
            </h2>
            <p>Bent u bereid de Inspectie SZW per direct onderzoek te laten doen naar deze situatie?
               Zo ja, op welke termijn kunt u de Kamer over de resultaten informeren? Zo nee, waarom
               niet?
            </p>
         </div>""")
        kamervraag = Kamervraag.objects.create(document=document, vraagnummer='dummy')
        openkamer.kamervraag.create_vragen_from_kamervraag_html(kamervraag)

    def test_create_kamervragen(self):
        n_create = 4
        kamervragen, kamerantwoorden = openkamer.kamervraag.create_kamervragen('2016', max_n=n_create, skip_if_exists=False)
        for kamervraag in kamervragen:
            self.assertTrue(kamervraag.kamerantwoord)
        self.assertEqual(len(kamervragen), n_create)
        self.assertEqual(len(kamerantwoorden), n_create)

    @staticmethod
    def get_tk_zaak(zaak_nummer):
        filter = Zaak.create_filter()
        filter.filter_nummer(zaak_nummer)
        tk_zaken = TKApi.get_zaken(filter=filter)
        return tk_zaken[0]

    @staticmethod
    def get_tk_document_for_zaak(zaak_nummer):
        tk_zaak = TestKamervraag.get_tk_zaak(zaak_nummer)
        for tk_doc in tk_zaak.documenten:
            if tk_doc.soort == DocumentSoort.SCHRIFTELIJKE_VRAGEN:
                return tk_doc
        return None

    def test_postponed_answer(self):
        zaak_nummer = '2017Z07318'
        tk_zaak = self.get_tk_zaak(zaak_nummer)
        overheid_id = 'kv-tk-{}'.format(zaak_nummer)
        kamervraag, kamerantwoord = openkamer.kamervraag.create_for_zaak(tk_zaak, overheid_id)
        self.assertIsNotNone(kamervraag)
        self.assertEqual(1, len(kamervraag.mededelingen))
        self.assertTrue(kamervraag.mededelingen[0].text)

    def test_update_or_create(self):
        zaak_nummer = '2017Z07318'
        tk_document = self.get_tk_document_for_zaak(zaak_nummer)
        overheid_doc_id = 'kv-tk-{}'.format(zaak_nummer)
        kamervraag = openkamer.kamervraag.create_kamervraag(tk_document, overheid_doc_id)
        documents = Document.objects.all()
        self.assertEqual(documents.count(), 1)
        kamervraag = openkamer.kamervraag.create_kamervraag(tk_document, overheid_doc_id)
        documents = Document.objects.all()
        self.assertEqual(documents.count(), 1)

    def test_get_tk_kamervraag_zaken(self):
        year = 2016
        month = 1
        begin_datetime = datetime.datetime(year=year, month=month, day=1)
        end_datetime = datetime.datetime(year=year + 1, month=month, day=1)
        infos = openkamer.kamervraag.get_tk_kamervraag_zaken(begin_datetime, end_datetime)
        self.assertEqual(len(infos), 2626)


class TestKamerantwoord(TestCase):

    def test_combined_answers(self):
        filter = TKDocument.create_filter()
        filter.filter_aanhangselnummer('151601580')
        docs = TKApi.get_documenten(filter=filter)
        self.assertEqual(1, len(docs))
        doc = docs[0]
        overheidnl_document_id = 'ah-tk-20152016-1580'
        kamerantwoord = openkamer.kamervraag.create_kamerantwoord(doc, overheidnl_document_id)
        self.assertEqual(4, kamerantwoord.antwoord_set.count())
        antwoorden = kamerantwoord.antwoord_set.all()
        self.assertEqual(None, antwoorden[0].see_answer_nr)
        self.assertEqual(None, antwoorden[1].see_answer_nr)
        self.assertEqual(2, antwoorden[2].see_answer_nr)
        self.assertEqual(None, antwoorden[3].see_answer_nr)


class TestVoting(TestCase):

    # TODO: test the following scenarios
    # voting withdrawn: 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P16766'
    # mistake: 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P10653'
    # no document id: 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2010P04136'
    # rijkswet: 'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/detail?id=2016P11874'

    # TODO: improve performance and enable
    # def test_voting_party_vote(self):
    #     Api(verbose=True)
    #     dossier_id = 33885
    #     Dossier.objects.create(dossier_id=dossier_id)
    #     besluiten = queries.get_dossier_besluiten_with_stemmingen(nummer=dossier_id)
    #     max_votings = 2
    #     voting_factory = openkamer.voting.VotingFactory(do_create_missing_party=False)
    #     for besluit in besluiten:
    #         voting_factory.create_votings_dossier_besluit(besluit, dossier_id)
    #     voting_factory.create_votings(dossier_id)

    # TODO: improve performance and enable
    # def test_voting_individual_vote(self):
    #     dossier_id = 33506
    #     Dossier.objects.create(dossier_id=dossier_id)
    #     voting_factory = openkamer.voting.VotingFactory(do_create_missing_party=False)
    #     voting_factory.create_votings(dossier_id)

    # def test_dossier_voting_controversieel(self):
    #     dossier_id = 29282
    #     dossier = Dossier.objects.create(dossier_id=dossier_id)
    #     besluit = self.get_besluit_kamerstuk(dossier_id, 337)
    #     voting_factory = openkamer.voting.VotingFactory()
    #     voting_factory.create_votings_dossier_besluit(besluit, dossier_id)
    #     votings = Voting.objects.all()
    #     self.assertEqual(votings.count(), 27)
    #     for voting in votings:
    #         self.assertEqual(dossier.id, voting.dossier.id)
    #     dossier.delete()
    #     votings = Voting.objects.all()
    #     self.assertEqual(votings.count(), 0)

    def test_get_voting_not_voted(self):
        dossier_id = 33542
        volgnummer = 39
        Dossier.objects.create(dossier_id=dossier_id)
        tk_besluit = self.get_besluit_kamerstuk(dossier_id=dossier_id, volgnummer=volgnummer)
        voting_factory = openkamer.voting.VotingFactory(do_create_missing_party=False)
        voting_factory.create_votings_dossier_besluit(tk_besluit, dossier_id)
        votings = Voting.objects.all()
        did_check = False
        for voting in votings:
            for vote in voting.votes:
                if vote.party_name == 'Van Vliet':
                    self.assertEqual(vote.decision, Vote.NONE)
                    did_check = True
        self.assertTrue(did_check)

    def get_besluit_kamerstuk(self, dossier_id, volgnummer):
        tk_besluiten = queries.get_kamerstuk_besluiten(nummer=dossier_id, volgnummer=volgnummer)
        self.assertEqual(1, len(tk_besluiten))
        tk_besluit = tk_besluiten[0]
        return tk_besluit


class TestDossierBesluit(TestCase):
    DOSSIER_ID = 34792

    def test_get_dossier_zaken(self):
        zaken = openkamer.dossier.get_zaken_dossier_main(dossier_id_main=self.DOSSIER_ID)
        self.assertEqual(1, len(zaken))

    def test_get_dossier_besluiten(self):
        besluiten = openkamer.dossier.get_tk_besluiten_dossier_main(dossier_id_main=self.DOSSIER_ID)
        # print('{} besluiten found'.format(len(besluiten)))
        # for index, besluit in enumerate(besluiten):
        #     print('{} | {} | {} besluit stemmingen'.format(index, besluit.tekst, len(besluit.stemmingen)))
        self.assertEqual(7, len(besluiten))

    def test_get_last_besluit(self):
        tk_besluit = openkamer.dossier.get_besluit_last(dossier_id_main=self.DOSSIER_ID)
        self.assertEqual(0, len(tk_besluit.stemmingen))

    def test_get_last_besluit_with_voting(self):
        tk_besluit = openkamer.dossier.get_besluit_last_with_voting(dossier_id_main=self.DOSSIER_ID)
        self.assertEqual(13, len(tk_besluit.stemmingen))


class TestGifts(TestCase):

    def test_create_gifts(self):
        openkamer.gift.create_gifts(max_items=20)


class TestVerslagAlgemeenOverleg(TestCase):

    def test_create_verslag(self):
        filter = TKDocument.create_filter()
        dossier_id = 26234
        kamerstuk_nr = 225
        filter.filter_dossier(dossier_id)
        filter.filter_volgnummer(kamerstuk_nr)
        docs = TKApi.get_documenten(filter=filter, max_items=10)
        self.assertEqual(1, len(docs))
        overheidnl_document_id = 'kst-{}-{}'.format(dossier_id, kamerstuk_nr)
        commissie = Commissie.objects.create(name='test commissie', name_short='tc', slug='tc')
        verslag = openkamer.verslagao.create_verslag(
            tk_document=docs[0],
            overheidnl_document_id=overheidnl_document_id,
            dossier_id=dossier_id,
            kamerstuk_nr=kamerstuk_nr,
            commissie=commissie
        )


class TestFindTKAPIPerson(TestCase):

    def test_find_person(self):
        person = Person(
            surname='Samsom',
            forename='Diederik'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, person.surname)

    def test_find_person_common_surname(self):
        person = Person(
            surname='Vries',
            initials='J.M.'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, person.surname)

    def test_find_person_bijsterveldt(self):
        person = Person(
            surname='Bijsterveldt',
            initials='J.M.'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, 'Bijsterveldt-Vliegenthart')

    def test_find_person_ozturk(self):
        person = Person(
            surname='Öztürk'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, 'Öztürk')

    def test_find_person_pater_postma(self):
        person = Person(
            surname='Pater-Postma',
            forename='Wytske',
            initials='W.L.'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, 'Postma')

    def test_find_person_arissen(self):
        person = Person(
            surname='Merel Arissen',
            forename='Femke',
            initials='F.M.'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, 'Kooten-Arissen')

    def test_find_person_common_surname_initials_without_dots(self):
        person = Person(
            surname='Vries',
            initials='JM'
        )
        tkperson = openkamer.parliament.find_tkapi_person(person)
        self.assertEqual(tkperson.achternaam, person.surname)
