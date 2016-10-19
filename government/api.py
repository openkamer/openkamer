from rest_framework import serializers, viewsets

from government.models import Government


class GovernmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Government
        fields = ('id', 'name', 'wikidata_id')


class GovernmentViewSet(viewsets.ModelViewSet):
    queryset = Government.objects.all()
    serializer_class = GovernmentSerializer
