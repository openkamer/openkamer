from django.db import models

from parliament.models import PoliticalParty
from parliament.models import ParliamentMember


class Dossier(models.Model):
    dossier_id = models.CharField(max_length=100, blank=True, unique=True)

    def __str__(self):
        return str(self.dossier_id)

    def documents(self):
        return Document.objects.filter(dossier=self)

    def kamerstukken(self):
        return Kamerstuk.objects.filter(document__dossier=self)

    def voting(self):
        votings = Voting.objects.filter(dossier=self, is_dossier_voting=True)
        if votings.exists():
            return votings[0]
        return None

    def title(self):
        kamerstukken = self.kamerstukken()
        titles = {}
        for stuk in kamerstukken:
            title = stuk.document.title()
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


class Document(models.Model):
    dossier = models.ForeignKey(Dossier, blank=True, null=True)
    document_id = models.CharField(max_length=200, blank=True)
    title_full = models.CharField(max_length=500)
    title_short = models.CharField(max_length=200)
    publication_type = models.CharField(max_length=200, blank=True)
    submitter = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    date_published = models.DateField(blank=True, null=True)
    content_html = models.CharField(max_length=200000, blank=True)

    def title(self):
        return self.title_full.split(';')[0]

    def document_url(self):
        return 'https://zoek.officielebekendmakingen.nl/' + str(self.document_id) + '.html'

    def __str__(self):
        return self.title_short

    class Meta:
        ordering = ['-date_published']


class Kamerstuk(models.Model):
    document = models.ForeignKey(Document)
    id_main = models.CharField(max_length=40, blank=True)
    id_sub = models.CharField(max_length=40, blank=True)
    type_short = models.CharField(max_length=40, blank=True)
    type_long = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return str(self.id_main) + '.' + str(self.id_sub) + ' ' + str(self.type_long)

    def voting(self):
        votings = Voting.objects.filter(kamerstuk=self)
        if votings.exists():
            return votings[0]
        return None

    def visible(self):
        if self.type_short == 'Koninklijke boodschap':
            return False
        return True

    def voorstelwet(self):
        if self.type_short == 'Voorstel van wet':
            return True
        return False

    class Meta:
        verbose_name_plural = 'Kamerstukken'
        ordering = ['id_sub']


class Voting(models.Model):
    AANGENOMEN = 'AAN'
    VERWORPEN = 'VER'
    INGETROKKEN = 'ING'
    AANGEHOUDEN = 'AGH'
    CHOICES = (
        (AANGENOMEN, 'Aangenomen'), (VERWORPEN, 'Verworpen'), (INGETROKKEN, 'Ingetrokken'), (AANGEHOUDEN, 'Aangehouden')
    )
    dossier = models.ForeignKey(Dossier)
    kamerstuk = models.ForeignKey(Kamerstuk, blank=True, null=True)
    is_dossier_voting = models.BooleanField(default=False)
    result = models.CharField(max_length=3, choices=CHOICES)
    date = models.DateField(auto_now=False, blank=True)

    def votes(self):
        return Vote.objects.filter(voting=self)

    def has_result_details(self):
        return self.votes().count() > 0

    def parties_for_string(self):
        parties_str = ''
        for vote in self.votes():
            if vote.decision == Vote.FOR:
                parties_str += vote.party.name_short + ', '
        return parties_str

    def parties_against_string(self):
        parties_str = ''
        for vote in self.votes():
            if vote.decision == Vote.AGAINST:
                parties_str += vote.party.name_short + ', '
        return parties_str

    def result_percent(self):
        n_votes = 0
        vote_for = 0
        vote_against = 0
        for vote in self.votes():
            n_votes += vote.number_of_seats
            if vote.decision == Vote.FOR:
                vote_for += vote.number_of_seats
            elif vote.decision == Vote.AGAINST:
                vote_against += vote.number_of_seats
        if n_votes == 0:
            return None
        for_percent = vote_for/n_votes * 100.0
        against_percent = vote_against/n_votes * 100.0
        return {'for': for_percent, 'against': against_percent}

    def __str__(self):
        return 'Dossier: ' + self.dossier.dossier_id + ', result: ' + self.result


class Vote(models.Model):
    FOR = 'FO'
    AGAINST = 'AG'
    CHOICES = (
        (FOR, 'For'), (AGAINST, 'Against'),
    )

    voting = models.ForeignKey(Voting)
    number_of_seats = models.IntegerField()
    decision = models.CharField(max_length=2, choices=CHOICES)
    details = models.CharField(max_length=2000, blank=True, null=False, default='')

    def __str__(self):
        return str(self.voting) + ' - ' + str(self.decision)


class VoteParty(Vote):
    party = models.ForeignKey(PoliticalParty)


class VoteIndividual(Vote):
    parliament_member = models.ForeignKey(ParliamentMember)
