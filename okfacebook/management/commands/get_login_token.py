import requests
import json

from django.core.management.base import BaseCommand

from django.conf import settings

import facebook


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('short_lived_token', nargs='+', type=str)

    def handle(self, *args, **options):
        url = 'https://graph.facebook.com/oauth/access_token'
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'fb_exchange_token': options['short_lived_token'][0]
        }
        response = requests.get(url, params=params)
        print(response.content)