from django.conf import settings

TWITTER_CONSUMER_KEY = getattr(settings, 'TWITTER_CONSUMER_KEY', '')
TWITTER_CONSUMER_SECRET = getattr(settings, 'TWITTER_CONSUMER_SECRET', '')
TWITTER_ACCESS_TOKEN_KEY = getattr(settings, 'TWITTER_ACCESS_TOKEN_KEY', '')
TWITTER_ACCESS_TOKEN_SECRET = getattr(settings, 'TWITTER_ACCESS_TOKEN_SECRET', '')
