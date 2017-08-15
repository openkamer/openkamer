# user settings, included in settings.py

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

# SECURITY WARNING: Make this unique, and don't share it with anybody.
SECRET_KEY = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'openkamer.sqlite'),                      # Or path to database file if using sqlite3.
    }
}

LANGUAGE_CODE = 'nl-NL'
TIME_ZONE = "Europe/Amsterdam"

ALLOWED_HOSTS = ['*']

#STATIC_ROOT = '/home/username/webapps/openkamerstatic/'
STATIC_ROOT = ''

# URL prefix for static files.
#STATIC_URL = '//www.openkamer.org/static/'
STATIC_URL = '/static/'

#MEDIA_ROOT = '/home/<username>/webapps/<projectstatic>/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'website/static/media/')

#MEDIA_URL = '//www.<your-domain>.com/static/media/'
MEDIA_URL = '/static/media/'

# DBBACKUP
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, STATIC_ROOT, 'backup/')}

# DJANGO-CRON
CRON_LOCK_DIR = '/tmp'
CRON_CLASSES = [
    # 'website.cron.TestJob',
    'website.cron.BackupDaily',
    # 'website.cron.CreateCommitPartyCSV',
    # 'website.cron.CreateCommitParliamentMembersCSV',
    # 'website.cron.CreateCommitWetsvoorstellenIDs',
    'website.cron.CleanUnusedPersons',
    # 'website.cron.UpdateSubmitters'
    # 'website.cron.UpdateParliamentAndGovernment',
    # 'website.cron.UpdateActiveDossiers',
    # 'website.cron.UpdateInactiveDossiers',
    # 'website.cron.UpdateBesluitenLijsten',
    # 'website.cron.UpdateKamervragenRecent',
    # 'website.cron.UpdateKamervragenAll',
    # 'oktwitter.cron.UpdateTwitterLists',
    # 'stats.cron.UpdateStatsData',
    # 'website.cron.UpdateSearchIndex',
]

# OPENKAMER
CONTACT_EMAIL = 'info@openkamer.org'
OK_TMP_DIR = os.path.join(BASE_DIR, 'data/tmp/')

# DOCUMENT
NUMBER_OF_LATEST_DOSSIERS = 6
AGENDAS_PER_PAGE = 50
DOSSIERS_PER_PAGE = 20
VOTINGS_PER_PAGE = 25
BESLUITENLIJSTEN_PER_PAGE = 200

# PIWIK
PIWIK_URL = ''  # optional, without trailing slash
PIWIK_SITE_ID = 0

# TWEEDEKAMER DATA REPO
GIT_AUTHOR_NAME = ''
GIT_AUTHOR_EMAIL = ''
DATA_REPO_DIR = '<path-to-repo>/ok-tk-data/'

# TWITTER
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN_KEY = ''
TWITTER_ACCESS_TOKEN_SECRET = ''
