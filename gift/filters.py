import logging

import django_filters

from gift.models import Gift

from document.filters import ModelSelect2SlugWidget
from person.models import Person
from parliament.models import PoliticalParty

logger = logging.getLogger(__name__)


class GiftFilter(django_filters.FilterSet):
    description = django_filters.CharFilter(method='gift_description_filter', label='')
    person = django_filters.ModelChoiceFilter(
        queryset=Person.objects.all(),
        to_field_name='slug',
        method='gift_person_filter',
        label='',
        widget=ModelSelect2SlugWidget(url='person-autocomplete')
    )
    party = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all().order_by('-current_parliament_seats'),
        to_field_name='slug',
        method='gift_party_filter',
        label='',
    )

    class Meta:
        model = Gift
        exclude = '__all__'

    def gift_description_filter(self, queryset, name, value):
        dossiers = queryset.filter(description__icontains=value).distinct()
        return dossiers

    def gift_person_filter(self, queryset, name, value):
        return queryset.filter(person=value)

    def gift_party_filter(self, queryset, name, value):
        return queryset.filter(person_position__party=value)
