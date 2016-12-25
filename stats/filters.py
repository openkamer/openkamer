from django import forms

import django_filters

from document.models import VoteParty


class PartyVotesFilter(django_filters.FilterSet):
    VOTING_TYPE_CHOICES = (
        ('BILL', 'Wetsvoorstel'),
        ('OTHER', 'Other')
    )
    type = django_filters.ChoiceFilter(method='type_filter', choices=VOTING_TYPE_CHOICES)

    class Meta:
        model = VoteParty
        exclude = '__all__'

    def type_filter(selfs, queryset, name, value):
        if value == 'BILL':
            return queryset.filter(voting__is_dossier_voting=True).distinct()
        elif value == 'OTHER':
            return queryset.filter(voting__is_dossier_voting=False).distinct()

