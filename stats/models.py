import datetime
import logging

from django.db import models
from django.db import transaction
from django.utils import timezone

from person.models import Person

from document.models import Kamervraag
from document.models import Kamerantwoord
from document.models import Vote
from document.models import Voting
from document.models import Submitter
from document.models import CategoryDocument

from government.models import Government
from government.models import Ministry
from parliament.models import PoliticalParty
from parliament.models import Parliament
from parliament.models import ParliamentMember

from stats import util

from stats.plots import PlotKamervraagVsTime
from stats.plots import PlotKamervraagVsTimePerParty
from stats.plots import PlotKamervraagReplyTimeContour
from stats.plots import PlotKamervraagReplyTimeHistogram
from stats.plots import PlotKamervraagVsTimePerPartySeat
from stats.plots import PlotKamervraagVsTimePerCategory
from stats.plots import PlotPartySeatsVsTime
from stats.plots import kamervragen_reply_time_per_party
from stats.plots import kamervragen_reply_time_per_ministry
from stats.plots import kamervragen_reply_time_per_year


logger = logging.getLogger(__name__)


def update_all():
    logger.info('BEGIN')
    start_date = datetime.date(year=2010, month=1, day=1)
    SeatsPerParty.create_or_update_all(start_date)
    StatsVotingSubmitter.create()
    PartyVoteBehaviour.create_all()
    Plot.create()
    logger.info('END')


class PartyVoteBehaviour(models.Model):
    BILL = 'BILL'
    OTHER = 'OTHER'
    VOTING_TYPE_CHOICES = (
        (BILL, 'Wetsvoorstel'),
        (OTHER, 'Overig (Motie, Amendement)')
    )
    party = models.ForeignKey(PoliticalParty)
    submitter = models.ForeignKey(PoliticalParty, related_name='party_vote_behaviour_submitter', blank=True, null=True)
    government = models.ForeignKey(Government)
    voting_type = models.CharField(max_length=5, choices=VOTING_TYPE_CHOICES)
    votes_for = models.IntegerField()
    votes_against = models.IntegerField()
    votes_none = models.IntegerField()

    def total_votes(self):
        return self.votes_for + self.votes_against + self.votes_none

    @staticmethod
    def get_stats_party(party, government=None, voting_type=None):
        """
        Returns voting behaviour stats for a given party during a given government period.

        :param party: the party for which to get the stats
        :param government: (optional) the government period for which to get the stats
        :param voting_type: (optional) the type of voting
        :return: a dictionary with basic voting stats
        """
        vote_behaviours = PartyVoteBehaviour.objects.filter(submitter__isnull=True)
        vote_behaviours = PartyVoteBehaviour.filter_by_type_and_government(vote_behaviours, voting_type=voting_type, government=government)
        return PartyVoteBehaviour.get_stats_party_for_qs(party, vote_behaviours)

    @staticmethod
    def get_stats_party_for_submitter(party_voting, party_submitting, government=None, voting_type=None):
        """
        Returns voting behaviour stats for a given party, for a given submitting party, during a given government period.

        :param party_voting: the party for which to get the stats
        :param party_submitting: the party who submitted/initiated the voting (or related document or bill)
        :param government: the government period for which to get the stats
        :param voting_type: (optional) the type of voting
        :return: a dictionary with basic voting stats
        """
        vote_behaviours = PartyVoteBehaviour.objects.filter(submitter=party_submitting)
        vote_behaviours = PartyVoteBehaviour.filter_by_type_and_government(vote_behaviours, voting_type=voting_type, government=government)
        return PartyVoteBehaviour.get_stats_party_for_qs(party_voting, vote_behaviours)

    @staticmethod
    def filter_by_type_and_government(vote_behaviours, voting_type=None, government=None):
        if government:
            vote_behaviours = vote_behaviours.filter(government=government)
        if voting_type:
            vote_behaviours = vote_behaviours.filter(voting_type=voting_type)
        return vote_behaviours

    @staticmethod
    @transaction.atomic
    def create_all():
        logger.info('BEGIN')
        vote_submitters = StatsVotingSubmitter.objects.all()
        party_ids = list(vote_submitters.values_list('party__id', flat=True))
        PartyVoteBehaviour.objects.all().delete()
        parties = PoliticalParty.objects.filter(id__in=party_ids)
        for party in parties:
            PartyVoteBehaviour.create(party)
        logger.info('END, number of objects created: ' + str(PartyVoteBehaviour.objects.all().count()))

    @staticmethod
    @transaction.atomic
    def create(party):
        logger.info('BEGIN for party: ' + str(party))
        governments = Government.objects.all()
        party_votes_per_gov = []
        for gov in governments:
            party_votes_per_gov.append({'government': gov, 'party_votes': util.get_party_votes_for_government(gov)})
        stats = []
        parties = PoliticalParty.objects.all()
        for party_submitting in parties:
            PartyVoteBehaviour.create_for_submitting_party(party, party_submitting, party_votes_per_gov)
        PartyVoteBehaviour.create_for_submitting_party(party, None, party_votes_per_gov)
        logger.info('END')
        return stats

    @staticmethod
    def create_for_submitting_party(party, party_submitting, party_votes_per_gov):
        for votes_for_gov in party_votes_per_gov:
            for voting_type in PartyVoteBehaviour.VOTING_TYPE_CHOICES:
                PartyVoteBehaviour.create_party_type_gov(
                    party=party,
                    party_votes=votes_for_gov['party_votes'],
                    party_submitting=party_submitting,
                    government=votes_for_gov['government'],
                    voting_type=voting_type[0]
                )

    @staticmethod
    def create_party_type_gov(party, party_votes, party_submitting, government, voting_type):
        if voting_type == PartyVoteBehaviour.BILL:
            party_votes = party_votes.filter(voting__is_dossier_voting=True)
        elif voting_type == PartyVoteBehaviour.OTHER:
            party_votes = party_votes.filter(voting__is_dossier_voting=False)
        else:
            assert False
        party_votes = party_votes.filter(party=party)
        if party_submitting is not None:
            voting_ids = PartyVoteBehaviour.get_voting_ids_submitted_by_party(party_submitting)
            party_votes = party_votes.filter(voting__in=voting_ids).distinct()
        votes_for = party_votes.filter(decision=Vote.FOR)
        votes_against = party_votes.filter( decision=Vote.AGAINST)
        votes_none = party_votes.filter(decision=Vote.NONE)
        PartyVoteBehaviour.objects.create(
            party=party,
            submitter=party_submitting,
            government=government,
            voting_type=voting_type,
            votes_for=votes_for.count(),
            votes_against=votes_against.count(),
            votes_none=votes_none.count()
        )

    @staticmethod
    def get_voting_ids_submitted_by_party(party):
        submitters = StatsVotingSubmitter.objects.filter(party=party).select_related('voting')
        voting_ids = set()
        for submitter in submitters:
            voting_ids.add(submitter.voting.id)
        return voting_ids

    @staticmethod
    def get_stats_party_for_qs(party, vote_behaviours):
        """
        Return the vote behaviour for a given party, based on a queryset.
        Warning: this QuerySet should be filtered on one or no submitter (party), NOT multiple submitter parties.
        This would give incorrect (unexpected) results because one voting can have multiple submitters,
        causing votes to be counted more than once.

        :param party: the party for which to return the vote behaviour
        :param vote_behaviours: PartyVoteBehaviour QuerySet that is filtered on one, and only one submitter party,
        or not filtered by submitter at all
        :return: a dictionary of party vote behaviour
        """
        vote_behaviours = vote_behaviours.filter(party=party)
        # we either filter by no submitter (any party), or one party
        vote_behaviours_any_party = vote_behaviours.filter(submitter__isnull=True)
        if vote_behaviours_any_party:
            vote_behaviours = vote_behaviours_any_party
        n_votes_for = 0
        n_votes_against = 0
        n_votes_none = 0
        for result in vote_behaviours:
            n_votes_for += result.votes_for
            n_votes_against += result.votes_against
            n_votes_none += result.votes_none
        n_votes = n_votes_for + n_votes_against + n_votes_none
        if n_votes == 0:
            for_percent = 0
            against_percent = 0
            none_percent = 0
        else:
            for_percent = n_votes_for / n_votes * 100.0
            against_percent = n_votes_against / n_votes * 100.0
            none_percent = n_votes_none / n_votes * 100.0
        result = {
            'party': party,
            'n_votes': n_votes,
            'n_for': n_votes_for,
            'n_against': n_votes_against,
            'n_none': n_votes_for,
            'for_percent': for_percent,
            'against_percent': against_percent,
            'none_percent': none_percent,
        }
        return result


class StatsVotingSubmitter(models.Model):
    voting = models.ForeignKey(Voting)
    person = models.ForeignKey(Person)
    party = models.ForeignKey(PoliticalParty, blank=True, null=True)

    @staticmethod
    @transaction.atomic
    def create():
        logger.info('BEGIN')
        StatsVotingSubmitter.objects.all().delete()
        votings = Voting.objects.all()
        for voting in votings:
            for submitter in voting.submitters:
                StatsVotingSubmitter.objects.create(
                    voting=voting,
                    person=submitter.person,
                    party=submitter.party
                )
        logger.info('END')


class SeatsPerParty(models.Model):
    date = models.DateField()
    party = models.ForeignKey(PoliticalParty)
    seats = models.IntegerField(default=0)
    datetime_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.party.name + ': ' + str(self.seats) + ' seats at ' + str(self.date)

    @staticmethod
    def create_or_update_all(start_date):
        parliament = Parliament.get_or_create_tweede_kamer()
        end_date = datetime.date.today()
        date = start_date
        while date <= end_date:
            SeatsPerParty.create_for_date(parliament, date)
            date += datetime.timedelta(days=1)
            print('next date: ' + str(date))

    @staticmethod
    @transaction.atomic
    def create_for_date(parliament, date):
        party_seats = {}
        members = parliament.get_members_at_date(date)
        for member in members:
            party = member.political_party()
            if not party:
                logger.warning('no party found')
                logger.warning('member.person: ' + str(member.person))
                continue
            if party in party_seats:
                party_seats[party] += 1
            else:
                party_seats[party] = 1
        for party in party_seats:
            # print(party)
            info = SeatsPerParty.objects.get_or_create(date=date, party=party, seats=party_seats[party])
            # print(info)

    @staticmethod
    def seats_at_date(party, date):
        infos = SeatsPerParty.objects.filter(date=date, party=party)
        if infos and infos.count() == 1:
            return infos[0].seats
        else:
            logger.warning('multiple entries for single date and party')
            logger.warning('party: ' + str(party))
            logger.warning('date: ' + str(date))
            logger.warning('number of objects: ' + str(infos.count()))
        return None


class Plot(models.Model):
    KAMERVRAAG_VS_TIME = 'KVT'
    KAMERVRAAG_VS_TIME_PARTY = 'KVTP'
    KAMERVRAAG_VS_TIME_PARTY_SEATS = 'KVTPS'
    KAMERVRAAG_VS_TIME_CATEGORY = 'KVTPCL'
    KAMERVRAAG_REPLY_TIME_HIST = 'KRTH'
    KAMERVRAAG_REPLY_TIME_2DHIST = 'KRT2D'
    KAMERVRAAG_REPLY_TIME_PER_PARTY = 'KRTPP'
    KAMERVRAAG_REPLY_TIME_PER_YEAR = 'KRTPY'
    KAMERVRAAG_REPLY_TIME_PER_MINISTRY = 'KRTPM'
    KAMERVRAAG_REPLY_TIME_PER_MINISTRY_POSITION = 'KRTPMP'
    KAMERVRAAG_REPLY_TIME_PER_POSITION = 'KRTPPO'
    SEATS_PER_PARTY_VS_TIME = 'SPPVT'
    PLOT_TYPES = (
        (KAMERVRAAG_VS_TIME, 'Kamervraag vs time'),
        (KAMERVRAAG_VS_TIME_PARTY, 'Kamervraag vs time per party'),
        (KAMERVRAAG_VS_TIME_PARTY_SEATS, 'Kamervraag vs time per party seat'),
        (KAMERVRAAG_VS_TIME_CATEGORY, 'Kamervraag vs time per category'),
        (KAMERVRAAG_REPLY_TIME_HIST, 'Kamervraag reply time histogram'),
        (KAMERVRAAG_REPLY_TIME_2DHIST, 'Kamervraag reply time 2D histogram'),
        (KAMERVRAAG_REPLY_TIME_PER_PARTY, 'Kamervraag reply time per party'),
        (KAMERVRAAG_REPLY_TIME_PER_YEAR, 'Kamervraag reply time per year'),
        (KAMERVRAAG_REPLY_TIME_PER_MINISTRY, 'Kamervraag reply time per ministerie'),
        (KAMERVRAAG_REPLY_TIME_PER_MINISTRY_POSITION, 'Kamervraag reply time per ministerie bewindspersoon'),
        (KAMERVRAAG_REPLY_TIME_PER_POSITION, 'Kamervraag reply time per minister of staatssecretaris'),
        (SEATS_PER_PARTY_VS_TIME, 'Seats per party vs time'),
    )
    type = models.CharField(max_length=10, choices=PLOT_TYPES, default=KAMERVRAAG_VS_TIME, db_index=True)
    html = models.TextField()
    datetime_updated = models.DateTimeField(auto_now=True)

    party_slugs = ['pvv', 'sp', 'cda', 'd66', 'vvd', 'pvda', 'gl', 'cu', 'pvdd', 'sgp']

    class Meta:
        ordering = ['-datetime_updated']


    @staticmethod
    def create():
        logger.info('BEGIN')
        start_year = None
        # start_year = 2017
        # Plot.create_kamervragen_general_plots(start_year)
        # Plot.create_kamervragen_vs_time_party_plots(start_year)
        # Plot.create_kamervragen_party_plots(start_year)
        # Plot.create_kamervragen_ministry_plots(start_year)
        # Plot.create_kamervragen_years_plots(start_year)
        # Plot.create_kamervragen_vs_time_party_seats_plots(start_year)
        Plot.create_kamervragen_per_category_plot(start_year)
        # Plot.create_party_seats_vs_time_plot(start_year)
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_general_plots(start_year=None):
        logger.info('BEGIN')
        kamervragen = Kamervraag.objects.filter(kamerantwoord__isnull=False).select_related('document').distinct()
        if start_year:
            kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
        kamervraag_dates = []
        for kamervraag in kamervragen:
            kamervraag_dates.append(kamervraag.document.date_published)
        kamervraag_durations = []
        for kamervraag in kamervragen:
            kamervraag_durations.append(kamervraag.duration)
        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_VS_TIME)
        plot.html = PlotKamervraagVsTime(kamervraag_dates).create_plot()
        plot.save()
        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_HIST)
        plot.html = PlotKamervraagReplyTimeHistogram(kamervraag_durations).create_plot()
        plot.save()
        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_2DHIST)
        plot.html = PlotKamervraagReplyTimeContour(kamervraag_dates, kamervraag_durations).create_plot()
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_party_plots(start_year=None):
        logger.info('BEGIN')
        party_slugs = Plot.party_slugs
        party_labels = []
        party_durations = []
        for party_slug in party_slugs:
            submitters = Submitter.objects.filter(party_slug=party_slug)
            submitter_ids = list(submitters.values_list('id', flat=True))
            kamervragen = Kamervraag.objects.filter(document__submitter__in=submitter_ids, kamerantwoord__isnull=False).select_related('document').distinct()
            if start_year:
                kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
            kamervraag_durations = []
            for kamervraag in kamervragen:
                kamervraag_durations.append(kamervraag.duration)
            party = PoliticalParty.objects.get(slug=party_slug)
            party_labels.append(party.name_short + ' (' + str(kamervragen.count()) + ')')
            party_durations.append(kamervraag_durations)

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_PER_PARTY)
        plot.html = kamervragen_reply_time_per_party(party_labels, party_durations)
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_ministry_plots(start_year=None):
        logger.info('BEGIN')
        rutte_2 = Government.objects.filter(slug='kabinet-rutte-ii')[0]
        ministries = rutte_2.ministries

        ministry_names = []
        position_names = []
        ministry_durations = []
        position_durations = []
        position_types = {}

        for ministry in ministries:
            ministry_person_ids = []
            positions = ministry.positions()
            for position in positions:
                position_person_ids = []
                members = position.members
                for member in members:
                    ministry_person_ids.append(member.person.id)
                    position_person_ids.append(member.person.id)
                submitters = Submitter.objects.filter(person__in=position_person_ids)
                submitter_ids = list(submitters.values_list('id', flat=True))
                antwoorden = Kamerantwoord.objects.filter(
                    document__submitter__in=submitter_ids,
                    document__date_published__gt=rutte_2.date_formed,
                ).select_related('document').distinct()
                kamervragen = Kamervraag.objects.filter(kamerantwoord__in=antwoorden)
                if start_year:
                    kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
                kamervraag_durations = []
                for kamervraag in kamervragen:
                    kamervraag_durations.append(kamervraag.duration)
                if kamervraag_durations:
                    position_durations.append(kamervraag_durations)
                    position_names.append(ministry.name + ' (' + position.get_position_display() + ') (' + str(kamervragen.count()) + ')')
                    if position.get_position_display() in position_types:
                        position_types[position.get_position_display()] += kamervraag_durations
                    else:
                        position_types[position.get_position_display()] = kamervraag_durations

            submitters = Submitter.objects.filter(person__in=ministry_person_ids)
            submitter_ids = list(submitters.values_list('id', flat=True))
            antwoorden = Kamerantwoord.objects.filter(
                document__submitter__in=submitter_ids,
                document__date_published__gt=rutte_2.date_formed,
            ).select_related('document').distinct()
            kamervragen = Kamervraag.objects.filter(kamerantwoord__in=antwoorden)
            if start_year:
                kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
            kamervraag_durations = []
            for kamervraag in kamervragen:
                kamervraag_durations.append(kamervraag.duration)
            if kamervraag_durations:
                ministry_durations.append(kamervraag_durations)
                ministry_names.append(ministry.name + ' (' + str(kamervragen.count()) + ')')

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_PER_MINISTRY)
        plot.html = kamervragen_reply_time_per_ministry(ministry_names, ministry_durations)
        plot.save()

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_PER_MINISTRY_POSITION)
        plot.html = kamervragen_reply_time_per_ministry(position_names, position_durations)
        plot.save()

        position_type_names = []
        position_type_durations = []
        for key in position_types:
            position_type_names.append(key + ' (' + str(len(position_types[key])) + ')')
            position_type_durations.append(position_types[key])
        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_PER_POSITION)
        plot.html = kamervragen_reply_time_per_ministry(position_type_names, position_type_durations)
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_years_plots(start_year):
        logger.info('BEGIN')
        years = []
        year_labels = []
        year_durations = []
        if start_year is None:
            start_year = 2011
        end_year = datetime.date.today().year
        year = start_year
        while year <= end_year:
            years.append(year)
            year += 1

        for year in years:
            kamervragen = Kamervraag.objects.filter(kamerantwoord__isnull=False).select_related('document').distinct()
            kamervragen = kamervragen.filter(
                document__date_published__gt=datetime.datetime(year=year, month=1, day=1),
                document__date_published__lt=datetime.datetime(year=year+1, month=1, day=1),
            )
            kamervraag_durations = []
            for kamervraag in kamervragen:
                kamervraag_durations.append(kamervraag.duration)
            year_durations.append(kamervraag_durations)
            year_labels.append(str(year) + ' (' + str(len(kamervraag_durations)) + ')')

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_REPLY_TIME_PER_YEAR)
        plot.html = kamervragen_reply_time_per_year(year_labels, year_durations)
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_vs_time_party_plots(start_year):
        logger.info('BEGIN')
        party_labels = []
        party_kamervragen_dates = []

        for party_slug in Plot.party_slugs:
            submitters = Submitter.objects.filter(party_slug=party_slug)
            submitter_ids = list(submitters.values_list('id', flat=True))
            kamervragen = Kamervraag.objects.filter(document__submitter__in=submitter_ids, kamerantwoord__isnull=False).select_related('document').distinct()
            if start_year:
                kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
            kamervraag_dates = []
            for kamervraag in kamervragen:
                kamervraag_dates.append(kamervraag.document.date_published)
            party = PoliticalParty.objects.get(slug=party_slug)
            party_labels.append(party.name_short)
            party_kamervragen_dates.append(kamervraag_dates)

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_VS_TIME_PARTY)
        plot.html = PlotKamervraagVsTimePerParty(party_labels, party_kamervragen_dates).create_plot()
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_vs_time_party_seats_plots(start_year):
        logger.info('BEGIN')
        party_labels = []
        party_kamervragen_dates = []
        party_seats = []

        for party_slug in Plot.party_slugs:
            submitters = Submitter.objects.filter(party_slug=party_slug)
            submitter_ids = list(submitters.values_list('id', flat=True))
            kamervragen = Kamervraag.objects.filter(document__submitter__in=submitter_ids, kamerantwoord__isnull=False).select_related('document').distinct()
            if start_year:
                kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
            kamervraag_dates = []
            for kamervraag in kamervragen:
                kamervraag_dates.append(kamervraag.document.date_published)
            party = PoliticalParty.objects.get(slug=party_slug)
            party_labels.append(party.name_short)
            party_kamervragen_dates.append(kamervraag_dates)
            seats = []
            for date in kamervraag_dates:
                seats.append(SeatsPerParty.seats_at_date(party, date))
            party_seats.append(seats)

        plot, created = Plot.objects.get_or_create(type=Plot.KAMERVRAAG_VS_TIME_PARTY_SEATS)
        plot.html = PlotKamervraagVsTimePerPartySeat(party_labels, party_kamervragen_dates, party_seats).create_plot()
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_party_seats_vs_time_plot(start_year):
        logger.info('BEGIN')
        party_labels = []
        dates = []
        seats = []
        data = {}
        infos = SeatsPerParty.objects.all().order_by('party', 'date')
        if start_year:
            infos = infos.filter(date__gte=datetime.datetime(year=start_year, month=1, day=1))
        for info in infos:
            party_name = info.party.name_short
            if party_name not in data:
                data[party_name] = []
            data[party_name].append([info.date, info.seats])
        for party_name in data:
            party_dates = []
            party_seats = []
            for date_seats in data[party_name]:
                party_dates.append(date_seats[0])
                party_seats.append(date_seats[1])
            dates.append(party_dates)
            seats.append(party_seats)
            party_labels.append(party_name)
        # print(data)
        plot, created = Plot.objects.get_or_create(type=Plot.SEATS_PER_PARTY_VS_TIME)
        plot.html = PlotPartySeatsVsTime(party_labels, dates, seats).create_plot()
        plot.save()
        logger.info('END')

    @staticmethod
    @transaction.atomic
    def create_kamervragen_per_category_plot(start_year):
        logger.info('BEGIN')

        kamervragen = Kamervraag.objects.filter(kamerantwoord__isnull=False).select_related('document').distinct()
        if start_year:
            kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
        kamervraag_dates_all = []
        for kamervraag in kamervragen:
            kamervraag_dates_all.append(kamervraag.document.date_published)

        labels_small = []
        labels_medium = []
        labels_large = []
        counts = []
        kamervragen_dates_small = []
        kamervragen_dates_medium = []
        kamervragen_dates_large = []
        # categories = CategoryDocument.objects.exclude(name='organisatie en beleid')
        categories = CategoryDocument.objects.all()

        for category in categories:
            kamervragen = Kamervraag.objects.filter(document__categories=category.id, kamerantwoord__isnull=False).select_related('document').distinct()
            if start_year:
                kamervragen = kamervragen.filter(document__date_published__gt=datetime.datetime(year=start_year, month=1, day=1))
            if kamervragen.count() < 100:
                continue
            kamervraag_dates = []
            for kamervraag in kamervragen:
                kamervraag_dates.append(kamervraag.document.date_published)
            print(category.name)
            print(kamervragen.count())
            label = category.name + ' (' + str(len(kamervraag_dates)) + ')'
            # if len(kamervraag_dates) > 1000:
            kamervragen_dates_large.append(kamervraag_dates)
            labels_large.append(label)
            counts.append(len(kamervraag_dates))
            # elif len(kamervraag_dates) > 400:
            #     kamervragen_dates_medium.append(kamervraag_dates)
            #     labels_medium.append(label)
            # elif len(kamervraag_dates) > 200:
            #     kamervragen_dates_small.append(kamervraag_dates)
            #     labels_small.append(label)
            # else:
            #     continue

        data_all = list(zip(counts, labels_large, categories, kamervragen_dates_large))
        data_all.sort(key=lambda value: value[0])
        data_all.reverse()
        data_all = list(zip(*data_all))
        counts_sorted = list(data_all[0])
        labels_sorted = list(data_all[1])
        categories_sorted = list(data_all[2])
        dates_sorted = list(data_all[3])

        plots_html, categories = PlotKamervraagVsTimePerCategory(labels_sorted, categories_sorted, dates_sorted, kamervraag_dates_all).create_plots()
        plots_html, categories = PlotKamervraagVsTimePerCategory(labels_sorted, categories_sorted, dates_sorted, kamervraag_dates_all).create_plots()

        PlotKamervraagOnderwerp.objects.all().delete()
        for i in range(0, len(plots_html)):
            plot, created = PlotKamervraagOnderwerp.objects.get_or_create(
                type=Plot.KAMERVRAAG_VS_TIME_CATEGORY,
                y_scale_type=PlotKamervraagOnderwerp.DIFFERENCE_FROM_MEAN_RELATIVE_ALL,
                category=categories[i],
            )
            plot.html = plots_html[i]
            plot.n_kamervragen = counts_sorted[i]
            plot.save()
        logger.info('END')


class PlotKamervraagOnderwerp(Plot):
    DIFFERENCE_FROM_MEAN_RELATIVE_ALL = 'DFMRA'
    Y_SCALE_TYPES = (
        (DIFFERENCE_FROM_MEAN_RELATIVE_ALL, 'Difference from the mean number of kamervragen per category, relative to total kamervragen'),
    )
    y_scale_type = models.CharField(max_length=10, choices=Y_SCALE_TYPES, default=DIFFERENCE_FROM_MEAN_RELATIVE_ALL, db_index=True)
    category = models.ForeignKey(CategoryDocument)
    n_kamervragen = models.IntegerField(default=0)
