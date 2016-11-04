from rest_framework import serializers, viewsets

from document.models import CategoryDocument, CategoryDossier
from document.models import Document, Kamerstuk, Dossier, Submitter
from document.models import Voting, VoteParty, VoteIndividual


class DossierCategorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = CategoryDossier
        fields = ('id', 'name',)


class DossierCategoryViewSet(viewsets.ModelViewSet):
    queryset = CategoryDossier.objects.all()
    serializer_class = DossierCategorySerializer


class DocumentCategorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = CategoryDocument
        fields = ('id', 'name',)


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    queryset = CategoryDocument.objects.all()
    serializer_class = DocumentCategorySerializer


class DossierSerializer(serializers.HyperlinkedModelSerializer):
    documents = serializers.HyperlinkedRelatedField(read_only=True,
                                                    view_name='document-detail',
                                                    many=True)

    kamerstukken = serializers.HyperlinkedRelatedField(read_only=True,
                                                       view_name='kamerstuk-detail',
                                                       many=True)

    class Meta:
        model = Dossier
        fields = ('id', 'dossier_id', 'categories', 'title', 'kamerstukken', 'documents')


class DossierViewSet(viewsets.ModelViewSet):
    queryset = Dossier.objects.all()
    serializer_class = DossierSerializer


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    submitters = serializers.HyperlinkedRelatedField(read_only=True,
                                                     view_name='submitter-detail',
                                                     many=True)

    class Meta:
        model = Document
        fields = (
            'id',
            'dossier',
            'document_id',
            'document_url',
            'title_full',
            'title_short',
            'publication_type',
            'submitters',
            'categories',
            'publisher',
            'date_published',
            # 'content_html'  # too large, needs link to content
        )


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


class SubmitterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Submitter
        fields = ('person', 'document')


class SubmitterViewSet(viewsets.ModelViewSet):
    queryset = Submitter.objects.all()
    serializer_class = SubmitterSerializer


class VotingSerializer(serializers.HyperlinkedModelSerializer):
    votes_party = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='voteparty-detail',
        many=True
    )

    votes_individual = serializers.HyperlinkedRelatedField(
        read_only=True,
        view_name='voteindividual-detail',
        many=True
    )

    class Meta:
        model = Voting
        fields = ('id', 'dossier', 'kamerstuk', 'date', 'result', 'result_percent', 'votes_party', 'votes_individual')


class VotingViewSet(viewsets.ModelViewSet):
    queryset = Voting.objects.all()
    serializer_class = VotingSerializer


class VotePartySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VoteParty
        fields = ('id', 'voting', 'decision', 'party', 'number_of_seats', 'details')


class VotePartyViewSet(viewsets.ModelViewSet):
    queryset = VoteParty.objects.all()
    serializer_class = VotePartySerializer


class VoteIndividualSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VoteIndividual
        fields = ('id', 'voting', 'decision', 'parliament_member', 'number_of_seats', 'details')


class VoteIndividualViewSet(viewsets.ModelViewSet):
    queryset = VoteIndividual.objects.all()
    serializer_class = VoteIndividualSerializer

