# user settings, included in settings.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

# SECURITY WARNING: Make this unique, and don't share it with anybody.
SECRET_KEY = ''

LANGUAGE_CODE = 'nl-NL'
TIME_ZONE = "Europe/Amsterdam"

ALLOWED_HOSTS = ['*']

#STATIC_ROOT = '/home/username/webapps/openkamerstatic/'
STATIC_ROOT = ''

# URL prefix for static files.
#STATIC_URL = 'http://www.openkamer.org/static/'
STATIC_URL = '/static/'

#MEDIA_ROOT = '/home/<username>/webapps/<projectstatic>/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'website/static/media/')

#MEDIA_URL = 'http://www.<your-domain>.com/static/media/'
MEDIA_URL = '/static/media/'

# DOCUMENT
DOSSIERS_PER_PAGE = 20
VOTINGS_PER_PAGE = 25
BESLUITENLIJSTEN_PER_PAGE = 200

# PIWIK
PIWIK_URL = ''  # optional, without trailing slash
PIWIK_SITE_ID = 0
