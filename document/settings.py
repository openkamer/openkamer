from django.conf import settings

DOSSIERS_PER_PAGE = getattr(settings, 'DOSSIERS_PER_PAGE', 20)
VOTINGS_PER_PAGE = getattr(settings, 'VOTINGS_PER_PAGE', 50)