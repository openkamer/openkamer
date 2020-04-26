import datetime
import logging
import requests
from itertools import chain

from django.db import models
from django.utils.text import slugify
from django.utils.functional import cached_property

from tkapi.besluit import BesluitStatus as TKBesluitStatus

from person.models import Person

from parliament.models import PoliticalParty
from parliament.models import ParliamentMember
from parliament.models import PartyMember
from parliament.models import Commissie

from government.models import GovernmentMember

logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, default='')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CategoryDossier(Category):

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category (dossier)'
        verbose_name_plural = 'Categories (dossier)'


class CategoryDocument(Category):

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category (document)'
        verbose_name_plural = 'Categories (document)'


class Dossier(models.Model):
    AANGENOMEN = 'AAN'
    VERWORPEN = 'VER'
    INGETROKKEN = 'ING'
    AANGEHOUDEN = 'AGH'
    IN_BEHANDELING = 'INB'
    CONTROVERSIEEL = 'CON'
    ONBEKEND = 'ONB'
    CHOICES = (
        (AANGENOMEN, 'Aangenomen'), (VERWORPEN, 'Verworpen'), (INGETROKKEN, 'Ingetrokken'),
        (AANGEHOUDEN, 'Aangehouden'), (IN_BEHANDELING, 'In behandeling'), (CONTROVERSIEEL, 'Controversieel'), (ONBEKEND, 'Onbekend')
    )
    dossier_id = models.CharField(max_length=100, blank=True, unique=True, db_index=True)
    dossier_main_id = models.CharField(max_length=100, blank=True, db_index=True)
    dossier_sub_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=2000, blank=True, db_index=True)
    categories = models.ManyToManyField(CategoryDossier, blank=True)
    url = models.URLField(blank=True, max_length=1000)
    decision_text = models.CharField(max_length=2000, blank=True)
    status = models.CharField(max_length=3, choices=CHOICES, default=ONBEKEND, db_index=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-dossier_id']
        unique_together = ['dossier_main_id', 'dossier_sub_id']

    def __str__(self):
        return str(self.dossier_id)

    @staticmethod
    def create_dossier_id(main_id, sub_id) -> str:
        if sub_id:
            return '{}-{}'.format(main_id, sub_id)
        return main_id

    @staticmethod
    def split_dossier_id(dossier_id):
        dossier_ids = dossier_id.split('-')
        dossier_id_main = dossier_ids[0]
        dossier_id_sub = None
        if len(dossier_ids) > 1:
            dossier_id_sub = dossier_ids[1]
        return dossier_id_main, dossier_id_sub

    @cached_property
    def documents(self):
        return Document.objects.filter(dossier=self)

    @cached_property
    def kamerstukken(self):
        return Kamerstuk.objects.filter(document__dossier=self).select_related('document')

    @cached_property
    def decisions(self):
        return Decision.objects.filter(dossier=self)

    @cached_property
    def start_date(self):
        documents = Document.objects.filter(dossier=self).order_by('date_published')
        if documents.exists():
            return documents[0].date_published
        return None

    @cached_property
    def last_date(self):
        kamerstukken = Kamerstuk.objects.filter(id_main=self).order_by('-document__date_published').select_related('document')
        if kamerstukken.exists():
            if self.voting and self.voting.date > kamerstukken[0].document.date_published:
                return self.voting.date
            else:
                return kamerstukken[0].document.date_published
        return None

    @cached_property
    def voting(self):
        votings = Voting.objects.filter(dossier=self.id, is_dossier_voting=True).exclude(result=Voting.AANGEHOUDEN)
        if votings.exists():
            # if votings.count() > 1:
            #     logger.error('more than one dossier voting found for dossier ' + str(self.dossier_id))
            return votings[0]
        return None

    def set_derived_fields(self):
        self.status = self.get_status()
        self.title = self.get_title()
        self.save()

    def get_status(self):
        if self.is_withdrawn:
            return Dossier.INGETROKKEN
        elif self.passed:
            return Dossier.AANGENOMEN
        elif self.voting and self.voting.result == Voting.VERWORPEN:
            return Dossier.VERWORPEN
        elif self.voting and self.voting.result == Voting.CONTROVERSIEEL:
            return Dossier.CONTROVERSIEEL
        return Dossier.IN_BEHANDELING

    def get_title(self):
        if self.title:
            return self.title
        kamerstukken = self.kamerstukken
        titles = {}
        for stuk in kamerstukken:
            title = stuk.document.title
            if title in titles:
                titles[title] += 1
            else:
                titles[title] = 1
        max_titles = 0
        title = 'undefined'
        for key, value in titles.items():
            if value > max_titles:
                title = key
                max_titles = value
        return title

    @cached_property
    def is_withdrawn(self):
        kamerstukken = self.kamerstukken
        if kamerstukken:
            return 'intrekking' in kamerstukken[0].type_long.lower()  # latest kamerstuk
        return False

    @cached_property
    def passed(self):
        if 'aangenomen' in self.decision_text.lower():
            return True
        voting = self.voting
        if voting and voting.result == Voting.AANGENOMEN:
            return True
        return False

    @cached_property
    def first_voorstel(self):
        for kamerstuk in self.kamerstukken.reverse():
            if kamerstuk.voorstelwet:
                return kamerstuk
        return None

    @cached_property
    def is_active(self):
        status_active = [Dossier.IN_BEHANDELING, Dossier.AANGEHOUDEN, Dossier.ONBEKEND]
        if self.status in status_active:
            return True
        return False

    @staticmethod
    def get_lines_from_url(url):
        response = requests.get(url, timeout=60)
        return response.content.decode('utf-8').splitlines()


class Document(models.Model):
    dossier = models.ForeignKey(Dossier, blank=True, null=True, on_delete=models.CASCADE)
    document_id = models.CharField(unique=True, max_length=200, blank=True, db_index=True)
    title_full = models.CharField(max_length=3000)
    title_short = models.CharField(max_length=2000)
    publication_type = models.CharField(max_length=200, blank=True)
    types = models.CharField(max_length=2000, blank=True)
    categories = models.ManyToManyField(CategoryDocument, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    date_published = models.DateField(blank=True, null=True, db_index=True)
    source_url = models.URLField(max_length=1000)
    content_html = models.CharField(max_length=10000000, blank=True)
    date_updated = models.DateTimeField(auto_now=True)

    @cached_property
    def submitters(self):
        return Submitter.objects.filter(document=self, type=Submitter.SUBMITTER).exclude(person__surname='').select_related('person', 'document')

    @cached_property
    def receivers(self):
        return Submitter.objects.filter(document=self, type=Submitter.RECEIVER).exclude(person__surname='').select_related('person', 'document')

    @cached_property
    def title(self):
        return self.title_full.split(';')[0]

    @cached_property
    def document_url(self):
        if self.source_url:
            return self.source_url
        return 'https://zoek.officielebekendmakingen.nl/' + str(self.document_id) + '.html'

    @cached_property
    def foot_notes(self):
        return self.footnote_set.all()

    def __str__(self):
        return self.title_short

    class Meta:
        ordering = ['-date_published']


class Submitter(models.Model):
    SUBMITTER = 'submitter'
    RECEIVER = 'receiver'
    TYPE_CHOICES = (
        (SUBMITTER, SUBMITTER), (RECEIVER, RECEIVER)
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    party_slug = models.CharField(max_length=500, blank=True, default='', db_index=True)
    type = models.CharField(choices=TYPE_CHOICES, default=SUBMITTER, max_length=30, db_index=True, null=False)

    class Meta:
        unique_together = ['person', 'document']

    def __str__(self):
        return self.person.fullname()

    def update_submitter_party_slug(self):
        party = self.get_party()
        if party:
            self.party_slug = party.slug
        else:
            self.party_slug = ''
        self.save()

    @cached_property
    def government_members(self):
        """ :returns the government members of this person at the time the document was published """
        date = self.document.date_published
        return GovernmentMember.find_for_person(self.person, date)

    @cached_property
    def party(self):
        if not self.party_slug:
            return None
        parties = PoliticalParty.objects.filter(slug=self.party_slug)
        if parties:
            return parties[0]
        return None

    def get_party(self):
        """ this non cached version is needed for cron jobs that gave cache errors when using the cached_property """
        if self.person.surname == '' or not self.document:
            return None
        members = PartyMember.get_at_date(person=self.person, date=self.document.date_published)
        if members.exists():
            return members[0].party
        return None


class Kamerantwoord(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    vraagnummer = models.CharField(max_length=200, db_index=True)

    @cached_property
    def antwoorden(self):
        return self.antwoord_set.all()


class Kamervraag(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    vraagnummer = models.CharField(max_length=200, db_index=True)
    kamerantwoord = models.OneToOneField(Kamerantwoord, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-document__date_published']

    @cached_property
    def vragen(self):
        return self.vraag_set.all()

    @cached_property
    def antwoorden(self):
        if not self.kamerantwoord:
            return None
        return Antwoord.objects.filter(kamerantwoord=self.kamerantwoord)

    @cached_property
    def mededelingen(self):
        return KamervraagMededeling.objects.filter(kamervraag=self)

    @cached_property
    def duration(self):
        if not self.kamerantwoord:
            return (datetime.date.today() - self.document.date_published).days
        return (self.kamerantwoord.document.date_published - self.document.date_published).days


class Vraag(models.Model):
    nr = models.IntegerField(db_index=True)
    kamervraag = models.ForeignKey(Kamervraag, on_delete=models.CASCADE)
    text = models.CharField(max_length=50000)

    class Meta:
        ordering = ['nr']

    @cached_property
    def antwoord(self):
        if not self.kamervraag.antwoorden:
            return None
        antwoorden = self.kamervraag.antwoorden.filter(nr=self.nr)
        if antwoorden:
            return antwoorden[0]
        return None


class Antwoord(models.Model):
    nr = models.IntegerField(db_index=True)
    kamerantwoord = models.ForeignKey(Kamerantwoord, on_delete=models.CASCADE)
    text = models.CharField(max_length=50000)
    see_answer_nr = models.IntegerField(null=True, blank=False)

    class Meta:
        ordering = ['nr']

    def __str__(self):
        return 'Antwoord ' + str(self.nr) + ' deel van ' + str(self.kamerantwoord.id)


class FootNote(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    nr = models.IntegerField(db_index=True)
    text = models.CharField(max_length=10000, blank=True, default='')
    url = models.URLField(max_length=1000, blank=True, default='')

    class Meta:
        ordering = ['nr']


class KamervraagMededeling(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    vraagnummer = models.CharField(max_length=200, db_index=True)
    kamervraag = models.ForeignKey(Kamervraag, null=True, blank=True, on_delete=models.CASCADE)
    text = models.TextField()


class Kamerstuk(models.Model):
    MOTIE = 'Motie'
    AMENDEMENT = 'Amendement'
    WETSVOORSTEL = 'Wetsvoorstel'
    VERSLAG = 'Verslag'
    NOTA = 'Nota'
    BRIEF = 'Brief'
    UNKNOWN = 'Onbekend'
    VERSLAG_AO = 'VerslagAlgemeenOverleg'
    TYPE_CHOICES = (
        (MOTIE, MOTIE), (AMENDEMENT, AMENDEMENT), (WETSVOORSTEL, WETSVOORSTEL),
        (VERSLAG, VERSLAG), (NOTA, NOTA), (BRIEF, BRIEF),  (VERSLAG_AO, 'Verslag van een algemeen overleg'),
        (UNKNOWN, UNKNOWN)
    )
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    id_main = models.CharField(max_length=40, blank=True, db_index=True)  # dossier vetnummer/ID
    id_sub = models.CharField(max_length=40, blank=True, db_index=True)  # kamerstuk ondernummer
    type_short = models.CharField(max_length=400, blank=True)
    type_long = models.CharField(max_length=2000, blank=True)
    original_id = models.CharField(max_length=40, blank=True, db_index=True)  # format: 33885-[XVI]-22
    date_updated = models.DateTimeField(auto_now=True)
    type = models.CharField(choices=TYPE_CHOICES, default=UNKNOWN, max_length=30, db_index=True)

    class Meta:
        verbose_name_plural = 'Kamerstukken'
        ordering = ['-document__date_published', '-id_sub',]
        index_together = ['id_main', 'id_sub']
        # unique_together = ['id_main', 'id_sub']

    def save(self, *args, **kwargs):
        type = self.get_type()
        if type:
            self.type = type
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id_main) + '-' + str(self.id_sub) + ': ' + str(self.type_long)

    def get_type(self):
        if 'nota' in self.type_short.lower():
            return Kamerstuk.NOTA
        elif 'motie' in self.type_short.lower():
            return Kamerstuk.MOTIE
        elif 'amendement' in self.type_short.lower():
            return Kamerstuk.AMENDEMENT
        elif self.voorstelwet:
            return Kamerstuk.WETSVOORSTEL
        elif 'verslag van een algemeen overleg' in self.type_long.lower():
            return Kamerstuk.VERSLAG_AO
        elif 'verslag' in self.type_short.lower():
            return Kamerstuk.VERSLAG
        elif 'brief' in self.type_short.lower():
            return Kamerstuk.BRIEF
        return None

    @cached_property
    def id_full(self):
        return str(self.id_main) + '-' + str(self.id_sub)

    @cached_property
    def voting(self):
        votings = Voting.objects.filter(kamerstuk=self).select_related('kamerstuk').order_by('-date')
        if votings.exists():
            return votings[0]
        return None

    @cached_property
    def decisions(self):
        return Decision.objects.filter(kamerstuk=self).select_related('kamerstuk').order_by('-datetime')

    @cached_property
    def visible(self):
        if self.type_short == 'Koninklijke boodschap':
            return False
        return True

    @cached_property
    def voorstelwet(self):
        if 'voorstel van wet' in self.type_short.lower():
            return True
        return False

    @cached_property
    def original(self):
        if not self.original_id:
            return None
        ids = self.original_id.split('-')
        main_id = ids[0]
        sub_id = None
        if len(ids) == 2:  # Example: 33885-voorstel_van_wet
            sub_id = ids[1]
        if len(ids) == 3:  # Example: 35300-XVI-voorstel_van_wet
            main_id = '{}-{}'.format(ids[0], ids[1])
            sub_id = ids[2]
        if ids[1] == 'voorstel_van_wet':
            kamerstukken = Kamerstuk.objects.filter(id_main=ids[0]).exclude(id=self.id)
            for stuk in kamerstukken:
                if 'voorstel van wet' in stuk.type_short.lower() and 'gewijzigd' not in stuk.type_short.lower():
                    return stuk
        kamerstukken = Kamerstuk.objects.filter(id_main=main_id, id_sub=sub_id)
        if kamerstukken.exists():
            return kamerstukken[0]
        return None

    @cached_property
    def modifications(self):
        stukken = Kamerstuk.objects.filter(original_id=self.id_full)
        return stukken.order_by('document__date_published', 'id_sub')


class Agenda(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    agenda_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.document)


class AgendaItem(models.Model):
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE)
    dossier = models.ForeignKey(Dossier, null=True, on_delete=models.CASCADE)
    item_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.agenda)


class Decision(models.Model):
    tk_id = models.CharField(max_length=200, blank=True, db_index=True)
    datetime = models.DateTimeField(blank=True, null=True, db_index=True)
    dossier = models.ForeignKey(Dossier, blank=True, null=True, on_delete=models.CASCADE)
    kamerstuk = models.ForeignKey(Kamerstuk, blank=True, null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=200, choices=[(tag, tag.value) for tag in TKBesluitStatus], db_index=True)
    text = models.CharField(max_length=10000, blank=True)
    type = models.CharField(max_length=10000, blank=True)
    note = models.CharField(max_length=10000, blank=True)
    date_updated = models.DateTimeField(auto_now=True)


class Voting(models.Model):
    AANGENOMEN = 'AAN'
    VERWORPEN = 'VER'
    INGETROKKEN = 'ING'
    AANGEHOUDEN = 'AGH'
    CONTROVERSIEEL = 'CON'
    ONBEKEND = 'ONB'
    CHOICES = (
        (AANGENOMEN, 'Aangenomen'), (VERWORPEN, 'Verworpen'), (INGETROKKEN, 'Ingetrokken'),
        (AANGEHOUDEN, 'Aangehouden'), (CONTROVERSIEEL, 'Controversieel'), (ONBEKEND, 'Onbekend')
    )
    tk_id = models.CharField(max_length=200, blank=True, db_index=True)
    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE)
    decision = models.OneToOneField(Decision, blank=True, null=True, on_delete=models.CASCADE)
    kamerstuk = models.ForeignKey(Kamerstuk, blank=True, null=True, on_delete=models.CASCADE)
    kamerstuk_raw_id = models.CharField(max_length=200, blank=True, default='')
    is_dossier_voting = models.BooleanField(default=False)
    is_individual = models.BooleanField(default=False)
    result = models.CharField(max_length=3, choices=CHOICES, db_index=True)
    date = models.DateField(auto_now=False, blank=True, db_index=True)
    source_url = models.URLField(blank=True, default='', max_length=1000)
    date_updated = models.DateTimeField(auto_now=True)

    @cached_property
    def votes(self):
        return list(chain(self.votes_party, self.votes_individual))

    @cached_property
    def votes_for(self):
        return list(chain(
            VoteParty.objects.filter(voting=self, decision=Vote.FOR),
            VoteIndividual.objects.filter(voting=self, decision=Vote.FOR)
        ))

    @cached_property
    def votes_against(self):
        return list(chain(
            VoteParty.objects.filter(voting=self, decision=Vote.AGAINST),
            VoteIndividual.objects.filter(voting=self, decision=Vote.AGAINST)
        ))

    @cached_property
    def votes_none(self):
        return list(chain(
            VoteParty.objects.filter(voting=self, decision=Vote.NONE),
            VoteIndividual.objects.filter(voting=self, decision=Vote.NONE)
        ))

    @cached_property
    def votes_party(self):
        return VoteParty.objects.filter(voting=self).select_related('party')

    @cached_property
    def votes_individual(self):
        return VoteIndividual.objects.filter(voting=self).select_related('parliament_member')

    def has_result_details(self):
        return len(self.votes) > 0

    @cached_property
    def submitters(self):
        if self.is_dossier_voting and self.dossier.first_voorstel:
            return self.dossier.first_voorstel.document.submitters
        elif self.kamerstuk:
            return self.kamerstuk.document.submitters
        return []

    def entities_for_string(self):
        entities_str = ''
        for vote in self.votes:
            if vote.decision == Vote.FOR:
                entities_str += vote.get_name() + ', '
        return entities_str

    def entities_against_string(self):
        entities_str = ''
        for vote in self.votes:
            if vote.decision == Vote.AGAINST:
                entities_str += vote.get_name() + ', '
        return entities_str

    def entities_none_string(self):
        entities_str = ''
        for vote in self.votes:
            if vote.decision == Vote.NONE:
                entities_str += vote.get_name() + ', '
        return entities_str

    @cached_property
    def result_percent(self):
        n_votes = 0
        vote_for = 0
        vote_against = 0
        vote_none = 0
        for vote in self.votes:
            n_votes += vote.number_of_seats
            if vote.decision == Vote.FOR:
                vote_for += vote.number_of_seats
            elif vote.decision == Vote.AGAINST:
                vote_against += vote.number_of_seats
            elif vote.decision == Vote.NONE:
                vote_none += vote.number_of_seats
        if n_votes == 0:
            return None
        for_percent = vote_for/n_votes * 100.0
        against_percent = vote_against/n_votes * 100.0
        no_vote_percent = vote_none/n_votes * 100.0
        return {'for': for_percent, 'against': against_percent, 'no_vote': no_vote_percent}

    def __str__(self):
        return 'Dossier: ' + self.dossier.dossier_id + ', result: ' + self.result


class Vote(models.Model):
    FOR = 'FO'
    AGAINST = 'AG'
    NONE = 'NO'
    CHOICES = (
        (FOR, 'For'), (AGAINST, 'Against'), (NONE, 'None')
    )

    voting = models.ForeignKey(Voting, on_delete=models.CASCADE)
    number_of_seats = models.IntegerField()
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=200, blank=True, null=False, default='')
    is_mistake = models.BooleanField(default=False)

    def get_name(self):
        raise NotImplementedError

    def set_derived(self):
        raise NotImplementedError

    def __str__(self):
        return str(self.voting) + ' - ' + str(self.decision)


class VoteParty(Vote):
    party_name = models.CharField(max_length=300, blank=True)
    party = models.ForeignKey(PoliticalParty, blank=True, null=True, on_delete=models.SET_NULL)

    def set_derived(self):
        self.party = PoliticalParty.find_party(self.party_name)
        self.save()

    def get_name(self):
        if not self.party:
            return 'partij onbekend'
        return self.party.name_short


class VoteIndividual(Vote):
    person_name = models.CharField(max_length=500, blank=True)
    person_tk_id = models.CharField(max_length=200, blank=True, db_index=True)
    parliament_member = models.ForeignKey(ParliamentMember, blank=True, null=True, on_delete=models.SET_NULL)

    def set_derived(self):
        persons = Person.objects.filter(tk_id=self.person_tk_id)
        if not persons:
            logger.error('No person found for individual vote for name {} and tk_id {}'.format(self.person_name, self.person_tk_id))
            return
        members = ParliamentMember.find_at_date(persons[0], self.voting.date)
        if members:
            self.parliament_member = members[0]
            self.save()

    def get_name(self):
        return str(self.parliament_member)


class CommissieDocument(models.Model):
    document = models.ForeignKey(Document, null=False, on_delete=models.CASCADE)
    kamerstuk = models.ForeignKey(Kamerstuk, null=False, on_delete=models.CASCADE)
    commissie = models.ForeignKey(Commissie, null=False, on_delete=models.CASCADE)
