from django.conf.urls import url, include
from rest_framework import routers

from person.api import PersonViewSet
from government.api import GovernmentViewSet, MinistryViewSet, GovernmentPositionViewSet, GovernmentMemberViewSet
from parliament.api import ParliamentViewSet, ParliamentMemberViewSet
from parliament.api import PoliticalPartyViewSet, PartyMemberViewSet
from document.api import DocumentCategoryViewSet, DossierCategoryViewSet
from document.api import DocumentViewSet, KamerstukViewSet, DossierViewSet, SubmitterViewSet
from document.api import VotingViewSet, VotePartyViewSet, VoteIndividualViewSet

router = routers.DefaultRouter()

router.register(r'person', PersonViewSet)

router.register(r'parliament', ParliamentViewSet)
router.register(r'parliament_member', ParliamentMemberViewSet)
router.register(r'party', PoliticalPartyViewSet)
router.register(r'party_member', PartyMemberViewSet)

router.register(r'government', GovernmentViewSet)
router.register(r'ministry', MinistryViewSet)
router.register(r'government_position', GovernmentPositionViewSet)
router.register(r'government_member', GovernmentMemberViewSet)

router.register(r'category_dossier', DocumentCategoryViewSet)
router.register(r'category_document', DossierCategoryViewSet)
router.register(r'document', DocumentViewSet)
router.register(r'kamerstuk', KamerstukViewSet)
router.register(r'submitter', SubmitterViewSet)
router.register(r'dossier', DossierViewSet)
router.register(r'voting', VotingViewSet)
router.register(r'vote_party', VotePartyViewSet)
router.register(r'vote_individual', VoteIndividualViewSet)

urlpatterns = [
    url(r'', include(router.urls)),
]