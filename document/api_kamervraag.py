from rest_framework import serializers, viewsets

from document.models import Kamervraag, Kamerantwoord, Vraag, Antwoord
from document.models import Document, Submitter
from person.models import Person
from parliament.models import PoliticalParty


class KVPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = (
            'fullname', 'forename', 'surname', 'initials', 'wikidata_id', 'wikipedia_url',
            'parlement_and_politiek_id'
        )


class KVPoliticalPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = PoliticalParty
        fields = ('name_short', 'name', 'wikidata_id', 'wikipedia_url')


class KVSubmitterSerializer(serializers.ModelSerializer):
    person = KVPersonSerializer(read_only=True)
    party = KVPoliticalPartySerializer(read_only=True)

    class Meta:
        model = Submitter
        fields = ('person', 'party')


class KVDocumentSerializer(serializers.ModelSerializer):
    submitters = KVSubmitterSerializer(read_only=True, many=True)

    class Meta:
        model = Document
        fields = (
            'title_full', 'title_short', 'date_published',
            'source_url', 'submitters'
        )


class VraagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vraag
        fields = ('nr', 'text')


class AntwoordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Antwoord
        fields = ('nr', 'text')


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
    queryset = Kamervraag.objects.filter(kamerantwoord__isnull=False)
    serializer_class = KamervraagSerializer


class KamerantwoordViewSet(viewsets.ModelViewSet):
    allowed_methods = ('GET',)
    queryset = Kamerantwoord.objects.all()
    serializer_class = KamerantwoordSerializer
