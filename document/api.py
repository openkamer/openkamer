from rest_framework import serializers, viewsets

from document.models import Document, Kamerstuk


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'dossier_id', 'raw_type', 'raw_title', 'publisher', 'date_published', 'document_url')


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class KamerstukSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Kamerstuk
        fields = ('id', 'document', 'id_main', 'id_sub', 'type_short', 'type_long')


class KamerstukViewSet(viewsets.ModelViewSet):
    queryset = Kamerstuk.objects.all()
    serializer_class = KamerstukSerializer

