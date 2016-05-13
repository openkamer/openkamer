from django.conf.urls import url, include

from rest_framework import routers, serializers, viewsets


from parliament.models import Person, Parliament, ParliamentMember, PartyMember, PoliticalParty
from parliament.views import PersonsView


# Serializers define the API representation.
class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = ('forename', 'surname', 'surname_prefix', 'wikidata_uri')


class ParliamentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Parliament
        fields = ('name', 'wikidata_uri')


class ParliamentMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ParliamentMember
        fields = ('person', 'parliament', 'joined', 'left')


class PoliticalPartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PoliticalParty
        fields = ('name', 'founded', 'dissolved', 'logo', 'wikidata_uri')


class PartyMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PartyMember
        fields = ('person', 'party', 'joined', 'left')


# ViewSets define the view behavior.
class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer


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

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet)
router.register(r'parliament', ParliamentViewSet)
router.register(r'parliamentmember', ParliamentMemberViewSet)
router.register(r'party', PoliticalPartyViewSet)
router.register(r'partymember', PartyMemberViewSet)

urlpatterns = [
    url(r'^$', PersonsView.as_view()),
    url(r'^api/', include(router.urls)),
]