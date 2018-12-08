import logging

import django_filters

from travel.models import Travel

from document.filters import ModelSelect2SlugWidget
from person.models import Person
from parliament.models import PoliticalParty

logger = logging.getLogger(__name__)


class TravelFilter(django_filters.FilterSet):
    destination = django_filters.CharFilter(method='travel_destination_filter', label='')
    person = django_filters.ModelChoiceFilter(
        queryset=Person.objects.all(),
        to_field_name='slug',
        method='travel_person_filter',
        label='',
        widget=ModelSelect2SlugWidget(url='person-autocomplete')
    )
    party = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all().order_by('-current_parliament_seats'),
        to_field_name='slug',
        method='travel_party_filter',
        label='',
    )

    class Meta:
        model = Travel
        exclude = '__all__'

    def travel_destination_filter(self, queryset, name, value):
        dossiers = queryset.filter(destination__icontains=value).distinct()
        return dossiers

    def travel_person_filter(self, queryset, name, value):
        return queryset.filter(person=value)

    def travel_party_filter(self, queryset, name, value):
        return queryset.filter(person_position__party=value)
