from rest_framework import serializers, viewsets

from person.models import Person


class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = (
            'forename',
            'surname',
            'surname_prefix',
            'birthdate',
            'wikidata_uri',
            'wikimedia_image_name',
            'wikimedia_image_url',
        )


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
