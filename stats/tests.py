from django.test import TestCase

from stats.views import get_plot


class TestPlot(TestCase):

    def test_plot(self):
        request = None
        html = get_plot(request)
        print(html)
