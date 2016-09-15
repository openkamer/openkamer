from django.conf.urls import url, include
from rest_framework import routers

from person.api import PersonViewSet
from parliament.api import ParliamentViewSet, ParliamentMemberViewSet
from parliament.api import PoliticalPartyViewSet, PartyMemberViewSet
from document.api import DocumentViewSet, KamerstukViewSet, DossierViewSet
from document.api import VotingViewSet, VotePartyViewSet, VoteIndividualViewSet

router = routers.DefaultRouter()
router.register(r'person', PersonViewSet)
router.register(r'parliament', ParliamentViewSet)
router.register(r'parliamentmember', ParliamentMemberViewSet)
router.register(r'party', PoliticalPartyViewSet)
router.register(r'partymember', PartyMemberViewSet)
router.register(r'document', DocumentViewSet)
router.register(r'kamerstuk', KamerstukViewSet)
router.register(r'dossier', DossierViewSet)
router.register(r'voting', VotingViewSet)
router.register(r'voteparty', VotePartyViewSet)
router.register(r'voteindividual', VoteIndividualViewSet)

urlpatterns = [
    url(r'', include(router.urls)),
]