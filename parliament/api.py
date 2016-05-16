from rest_framework import serializers, viewsets

from parliament.models import Parliament, ParliamentMember, PartyMember, PoliticalParty


class ParliamentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Parliament
        fields = ('name', 'wikidata_id')


class ParliamentMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ParliamentMember
        fields = ('person', 'parliament', 'joined', 'left')


class PoliticalPartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PoliticalParty
        fields = ('name', 'name_short', 'founded', 'dissolved', 'wikidata_id', 'wikimedia_logo_url', 'wikipedia_url')


class PartyMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyMember
        fields = ('person', 'party', 'joined', 'left')


class ParliamentViewSet(viewsets.ModelViewSet):
    queryset = Parliament.objects.all()
    serializer_class = ParliamentSerializer


class ParliamentMemberViewSet(viewsets.ModelViewSet):
    queryset = ParliamentMember.objects.all()
    serializer_class = ParliamentMemberSerializer


class PoliticalPartyViewSet(viewsets.ModelViewSet):
    queryset = PoliticalParty.objects.all()
    serializer_class = PoliticalPartySerializer


class PartyMemberViewSet(viewsets.ModelViewSet):
    queryset = PartyMember.objects.all()
    serializer_class = PartyMemberSerializer
