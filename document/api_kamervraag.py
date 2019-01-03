import datetime

from rest_framework import serializers, viewsets

from person.models import Person
from parliament.models import PoliticalParty

from document.models import Kamervraag, Kamerantwoord, Vraag, Antwoord
from document.models import Document, Submitter, FootNote


class KVPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'fullname', 'forename', 'surname', 'initials', 'wikidata_id', 'wikipedia_url',
            'parlement_and_politiek_id'
        )


class KVSubmitterSerializer(serializers.ModelSerializer):
    person = KVPersonSerializer(read_only=True)

    class Meta:
        model = Submitter
        fields = ('person', 'party_slug')


class KVFootNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FootNote
        fields = ('nr', 'text', 'url')


class KVDocumentSerializer(serializers.ModelSerializer):
    submitters = KVSubmitterSerializer(read_only=True, many=True)
    foot_notes = KVFootNoteSerializer(read_only=True, many=True)

    class Meta:
        model = Document
        fields = (
            'title_full', 'title_short', 'date_published',
            'source_url', 'submitters', 'foot_notes'
        )


class VraagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vraag
        fields = ('nr', 'text')


class AntwoordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antwoord
        fields = ('nr', 'text', 'see_answer_nr')


class KamerantwoordSerializer(serializers.ModelSerializer):
    antwoorden = AntwoordSerializer(read_only=True, many=True)
    document = KVDocumentSerializer(read_only=True)

    class Meta:
        model = Kamerantwoord
        fields = ('url', 'document', 'vraagnummer', 'antwoorden')


class KamervraagSerializer(serializers.ModelSerializer):
    vragen = VraagSerializer(read_only=True, many=True)
    antwoorden = AntwoordSerializer(read_only=True, many=True)
    document = KVDocumentSerializer(read_only=True)

    class Meta:
        model = Kamervraag
        fields = ('url', 'vraagnummer', 'document', 'receiver', 'vragen', 'antwoorden')


class KamervraagViewSet(viewsets.ModelViewSet):
    allowed_methods = ('GET',)
    queryset = Kamervraag.objects.all()
    serializer_class = KamervraagSerializer

    def get_queryset(self):
        if 'year' in self.request.query_params:
            year = int(self.request.query_params['year'])
            begin_date = datetime.date(year=year, month=1, day=1)
            end_date = datetime.date(year=year + 1, month=1, day=1)
            kamervragen = Kamervraag.objects.filter(document__date_published__gt=begin_date).filter(document__date_published__lt=end_date)
        else:
            kamervragen = Kamervraag.objects.all()
        kamervragen = kamervragen.select_related('document')\
            .prefetch_related('vraag_set')\
            .prefetch_related('document__submitter_set')\
            .prefetch_related('document__footnote_set')
        return kamervragen


class KamerantwoordViewSet(viewsets.ModelViewSet):
    allowed_methods = ('GET',)
    queryset = Kamerantwoord.objects.all()
    serializer_class = KamerantwoordSerializer
