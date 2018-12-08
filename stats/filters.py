import logging

import django_filters

from document.models import VoteParty

from parliament.models import PoliticalParty
from government.models import Government

from stats.models import PartyVoteBehaviour

logger = logging.getLogger(__name__)


class PartyVotesFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(
        method='type_filter',
        choices=PartyVoteBehaviour.VOTING_TYPE_CHOICES,
    )
    submitter = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all().order_by('-current_parliament_seats'),
        to_field_name='slug',
        method='submitter_party_filter',
        label='',
    )
    government = django_filters.ModelChoiceFilter(
        queryset=Government.objects.all(),
        to_field_name='slug',
        method='government_filter',
        label='',
    )

    class Meta:
        model = VoteParty
        exclude = '__all__'

    def type_filter(selfs, queryset, name, value):
        return queryset.filter(voting_type=value)

    def submitter_party_filter(self, queryset, name, value):
        return queryset.filter(submitter=value)

    def government_filter(self, queryset, name, value):
        return queryset.filter(government=value)
