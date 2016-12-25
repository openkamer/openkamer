import django_filters

from document.models import VoteParty

from parliament.models import PoliticalParty
from parliament.models import PartyMember
from document.models import Document
from document.models import Submitter


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
        party_members = PartyMember.objects.filter(party=value).select_related('person')
        party_person_ids = []
        for member in party_members:
            party_person_ids.append(member.person.id)
        submitters = Submitter.objects.filter(person__in=party_person_ids).select_related('person')
        submitter_ids = []
        for submitter in submitters:
            pms = party_members.filter(person=submitter.person, joined__lte=submitter.document.date_published, left__gt=submitter.document.date_published) | \
                  party_members.filter(person=submitter.person, joined__lte=submitter.document.date_published, left__isnull=True) | \
                  party_members.filter(person=submitter.person, joined__isnull=True, left__isnull=True)
            if pms:
                submitter_ids.append(submitter.id)
        documents = Document.objects.filter(submitter__id__in=submitter_ids)
        votes = queryset.filter(voting__kamerstuk__document__in=documents)
        return votes
