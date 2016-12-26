import logging

import django_filters

from document.models import VoteParty

from parliament.models import PoliticalParty
from parliament.models import PartyMember
from document.models import Document
from document.models import Submitter

from stats.models import StatsVotingSubmitter

logger = logging.getLogger(__name__)


class PartyVotesFilter(django_filters.FilterSet):
    VOTING_TYPE_CHOICES = (
        ('BILL', 'Wetsvoorstel'),
        ('OTHER', 'Other (Moties, Amendementen)')
    )
    type = django_filters.ChoiceFilter(method='type_filter', choices=VOTING_TYPE_CHOICES)
    submitter = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all(),
        to_field_name='slug',
        method='submitter_party_filter',
        label='',
    )

    class Meta:
        model = VoteParty
        exclude = '__all__'

    def type_filter(selfs, queryset, name, value):
        if value == 'BILL':
            return queryset.filter(voting__is_dossier_voting=True).distinct()
        elif value == 'OTHER':
            return queryset.filter(voting__is_dossier_voting=False).distinct()

    def submitter_party_filter(self, queryset, name, value):
        submitters = StatsVotingSubmitter.objects.filter(party=value).select_related('voting')
        voting_ids = []
        for submitter in submitters:
            voting_ids.append(submitter.voting.id)
        votes = queryset.filter(voting__in=voting_ids).distinct()
        return votes
