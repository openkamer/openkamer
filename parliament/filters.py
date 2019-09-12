import django_filters

from parliament.models import PoliticalParty
from parliament.models import ParliamentMember


class ParliamentMemberFilter(django_filters.FilterSet):
    party = django_filters.ModelChoiceFilter(
        queryset=PoliticalParty.objects.all().order_by('-current_parliament_seats'),
        to_field_name='slug',
        method='party_filter',
        label='',
    )

    class Meta:
        model = ParliamentMember
        exclude = '__all__'

    def party_filter(self, queryset, name, value):
        pm_ids = []
        for pm in queryset:
            if pm.political_party().id == value.id:
                pm_ids.append(pm.id)
        return queryset.filter(id__in=pm_ids)
