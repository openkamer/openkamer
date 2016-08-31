from django.test import TestCase

from stats.views import get_example_plot_html_json


class TestPlot(TestCase):

    def test_plot(self):
        request = None
        html = get_example_plot_html_json(request)
