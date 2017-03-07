from django.test import TestCase

from document.models import Kamervraag

import openkamer.kamervraag


class TestKamervraag(TestCase):

    def test_create_kamervraag(self):
        infos = Kamervraag.get_kamervragen_info(2016)
        metadata = openkamer.kamervraag.create_kamervraag_document(infos[0])
        print(metadata)