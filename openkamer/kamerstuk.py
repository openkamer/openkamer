import logging
import re

from django.db import transaction

from document.models import Kamerstuk

logger = logging.getLogger(__name__)


@transaction.atomic
def create_kamerstuk(document, dossier_id, number, type_short, type_long):
    logger.info('BEGIN')
    original_id = find_original_kamerstuk_id(dossier_id, type_long)
    stuk = Kamerstuk.objects.create(
        document=document,
        id_main=dossier_id,
        id_sub=number,
        type_short=type_short,
        type_long=type_long,
        original_id=original_id
    )
    logger.info('kamerstuk created: {}'.format(stuk))
    logger.info('END')


def find_original_kamerstuk_id(dossier_id, type_long):
    if 'gewijzigd' not in type_long.lower() and 'nota van wijziging' not in type_long.lower():
        return ''
    result_dossier = re.search(r"t.v.v.\s*(?P<main_id>[0-9]{1,6}-[A-Z]{1,6})-(?P<sub_id>[0-9]*)", type_long)
    result_document = re.search(r"nr.\s*(?P<sub_id>[0-9]*)", type_long)
    main_id = ''
    sub_id = ''
    if result_dossier and 'main_id' in result_dossier.groupdict():
        main_id = result_dossier.group('main_id')
    if result_document and 'sub_id' in result_document.groupdict():
        sub_id = result_document.group('sub_id')
    if result_dossier and 'sub_id' in result_dossier.groupdict():
        sub_id = result_dossier.group('sub_id')
    if main_id and sub_id:
        return main_id + '-' + sub_id
    elif sub_id:
        return '{}-{}'.format(dossier_id , sub_id)
    elif 'voorstel van wet' in type_long.lower() or 'nota van wijziging' in type_long.lower():
        return '{}-voorstel_van_wet'.format(dossier_id)
    return ''
