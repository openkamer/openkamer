
import logging
logger = logging.getLogger(__name__)

from django.test import TestCase


class TestExample(TestCase):
    """ Example test case """

    def test_example(self):
        """ Example test """
        self.assertEqual(1, 1)
        self.assertTrue(True)
        self.assertFalse(False)