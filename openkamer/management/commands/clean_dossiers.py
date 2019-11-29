import logging

from django.core.management.base import BaseCommand

from document.create import get_dossier_ids
from document.models import Dossier

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        dossiers = get_dossier_ids()
        if len(dossiers) < 1500:
            logger.error('Less than 1500 dossiers found, something wrong, abort!')
            return
        dossiers_valid = []
        for dossier in dossiers:
            dossier_id = Dossier.create_dossier_id(dossier.dossier_id, dossier.dossier_sub_id)
            dossiers_valid.append(dossier_id)

        dossiers_to_delete = Dossier.objects.exclude(dossier_id__in=dossiers_valid)
        logger.info('Deleting ' + str(len(dossiers_to_delete)) + ' dossiers and related items')
        dossiers_to_delete.delete()
