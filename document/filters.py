from django import forms

from dal import autocomplete

import django_filters

from person.models import Person

from document.models import CategoryDossier
from document.models import CategoryDocument
from document.models import Dossier
from document.models import Kamervraag
from document.models import Voting


class ModelSelect2PersonWidget(autocomplete.ModelSelect2):

    def filter_choices_to_render(self, selected_choices):
        """Override from QuerySetSelectMixin to use the slug instead of pk (pk will change on database reset)"""
        self.choices.queryset = self.choices.queryset.filter(
            slug__in=[c for c in selected_choices if c]
        )


class DossierFilter(django_filters.FilterSet):
    DOSSIER_STATUS_CHOICES = (
        (Dossier.AANGENOMEN, 'Aangenomen'),
        (Dossier.VERWORPEN, 'Verworpen'),
        (Dossier.INGETROKKEN, 'Ingetrokken'),
        (Dossier.IN_BEHANDELING, 'In behandeling'),
        (Dossier.ONBEKEND, 'Onbekend'),
    )
    dossier_id = django_filters.CharFilter(method='dossier_id_filter', label='')
    title = django_filters.CharFilter(method='title_filter', label='')
    submitter = django_filters.ModelChoiceFilter(
        queryset=Person.objects.all(),
        to_field_name='slug',
        method='submitter_filter',
        label='',
        widget=ModelSelect2PersonWidget(url='person-autocomplete')
    )
    status = django_filters.ChoiceFilter(
        choices=DOSSIER_STATUS_CHOICES,
        method='status_filter',
        # widget=forms.ChoiceField()
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        name='categories',
        queryset=CategoryDossier.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Dossier
        exclude = '__all__'

    def title_filter(self, queryset, name, value):
        dossiers = queryset.filter(document__title_full__icontains=value).distinct()
        return dossiers

    def dossier_id_filter(selfs, queryset, name, value):
        return queryset.filter(dossier_id__icontains=value)

    def submitter_filter(self, queryset, name, value):
        dossiers = queryset.filter(document__submitter__person=value).distinct()
        return dossiers

    def status_filter(self, queryset, name, value):
        return queryset.filter(status=value)


class KamervraagFilter(django_filters.FilterSet):
    ANSWERED = 'beantwoord'
    UNANSWERED = 'onbeantwoord'
    KAMERVRAAG_STATUS_CHOICES = (
        (ANSWERED, 'Beantwoord'),
        (UNANSWERED, 'Onbeantwoord'),
    )
    title = django_filters.CharFilter(method='title_filter', label='')
    submitter = django_filters.ModelChoiceFilter(
        queryset=Person.objects.all(),
        to_field_name='slug',
        method='submitter_filter',
        label='',
        widget=ModelSelect2PersonWidget(url='person-autocomplete')
    )
    status = django_filters.ChoiceFilter(
        choices=KAMERVRAAG_STATUS_CHOICES,
        method='status_filter',
        # widget=forms.ChoiceField()
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        queryset=CategoryDocument.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        method='category_filter',
    )

    class Meta:
        model = Kamervraag
        exclude = '__all__'

    def title_filter(self, queryset, name, value):
        return queryset.filter(document__title_full__icontains=value).distinct()

    def submitter_filter(self, queryset, name, value):
        return queryset.filter(document__submitter__person=value).distinct()

    def category_filter(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(document__categories=value).distinct()

    def status_filter(self, queryset, name, value):
        if value == KamervraagFilter.ANSWERED:
            return queryset.filter(kamerantwoord__isnull=False)
        elif value == KamervraagFilter.UNANSWERED:
            return queryset.filter(kamerantwoord__isnull=True)
        return queryset


class VotingFilter(django_filters.FilterSet):
    VOTING_RESULT_CHOICES = (
        (Voting.AANGENOMEN, 'Aangenomen'),
        (Voting.VERWORPEN, 'Verworpen'),
        (Voting.INGETROKKEN, 'Ingetrokken'),
        (Voting.AANGEHOUDEN, 'Aangehouden'),
        (Voting.CONTROVERSIEEL, 'Controversieel'),
        (Voting.ONBEKEND, 'Onbekend'),
    )
    dossier_id = django_filters.CharFilter(method='dossier_id_filter', label='')
    title = django_filters.CharFilter(method='title_filter', label='')
    status = django_filters.ChoiceFilter(method='status_filter', choices=VOTING_RESULT_CHOICES)

    class Meta:
        model = Voting
        exclude = '__all__'

    def dossier_id_filter(selfs, queryset, name, value):
        return queryset.filter(dossier__dossier_id__icontains=value).distinct()

    def result_filter(self, queryset, name, value):
        return queryset.filter(result=value)

    def title_filter(self, queryset, name, value):
        return (queryset.filter(dossier__title__icontains=value) | queryset.filter(kamerstuk__type_long__icontains=value)).distinct()
