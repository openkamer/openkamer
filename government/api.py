from rest_framework import serializers, viewsets

from government.models import Government
from government.models import GovernmentPosition
from government.models import GovernmentMember
from government.models import Ministry


class GovernmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Government
        fields = ('id', 'name', 'wikidata_id', 'date_formed', 'date_dissolved')


class GovernmentViewSet(viewsets.ModelViewSet):
    queryset = Government.objects.all()
    serializer_class = GovernmentSerializer


class MinistrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ministry
        fields = ('id', 'name', 'government')


class MinistryViewSet(viewsets.ModelViewSet):
    queryset = Ministry.objects.all()
    serializer_class = MinistrySerializer


class GovernmentPositionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GovernmentPosition
        fields = ('id', 'position', 'ministry', 'government')


class GovernmentPositionViewSet(viewsets.ModelViewSet):
    queryset = GovernmentPosition.objects.all()
    serializer_class = GovernmentPositionSerializer


class GovernmentMemberSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GovernmentMember
        fields = ('id', 'person', 'position', 'start_date', 'end_date')


class GovernmentMemberViewSet(viewsets.ModelViewSet):
    queryset = GovernmentMember.objects.all()
    serializer_class = GovernmentMemberSerializer
