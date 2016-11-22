from django.conf import settings

NUMBER_OF_LATEST_DOSSIERS = getattr(settings, 'NUMBER_OF_LATEST_DOSSIERS', 6)
AGENDAS_PER_PAGE = getattr(settings, 'AGENDAS_PER_PAGE', 50)
DOSSIERS_PER_PAGE = getattr(settings, 'DOSSIERS_PER_PAGE', 20)
VOTINGS_PER_PAGE = getattr(settings, 'VOTINGS_PER_PAGE', 25)
BESLUITENLIJSTEN_PER_PAGE = getattr(settings, 'BESLUITENLIJSTEN_PER_PAGE', 200)