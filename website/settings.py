"""
Django settings for openkamer project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Application definition
INSTALLED_APPS = (
    'website',
    'openkamer',
    'stats',
    'oktwitter',
    'scraper',
    'document',
    'parliament',
    'government',
    'gift',
    'travel',
    'person',
    # 'debug_toolbar',
    'bootstrap3',
    'bootstrap_pagination',
    'rest_framework',
    'dal',
    'dal_select2',
    'django_filters',
    'dbbackup',
    'django_cron',
    'haystack',
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
)

MIDDLEWARE = [
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,"website")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.static',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'website.context_processors.version',
                'website.context_processors.piwik',
            ],
        },
    },
]


WSGI_APPLICATION = 'website.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

INTERNAL_IPS = ['127.0.0.1']  # needed for django-debug-toolbar

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'openkamer.sqlite'),                      # Or path to database file if using sqlite3.
    }
}

# DB dumps
JSON_DUMP_KEEP_DAYS = 3


##################
# LOCAL SETTINGS #
##################

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
from website.local_settings import *


##############
# Bootstrap3 #
##############

BOOTSTRAP3 = {
    'horizontal_label_class': 'col-md-2',
    'horizontal_field_class': 'col-md-4',
}

##########
# Search #
##########

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr/default5',
        'TIMEOUT': 3 * 60,
        # ...or for multicore...
        # 'URL': 'http://127.0.0.1:8983/solr/mysite',
    },
}

##################
# REST FRAMEWORK #
##################

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
    )
}

###########
# LOGGING #
###########

# Directory of the logfiles
LOG_DIR = os.path.join(BASE_DIR, 'log')

# Max. logfile size
LOGFILE_MAXSIZE = 10 * 1024 * 1024

# Number of old log files that are stored before they are deleted
# see https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler
LOGFILE_BACKUP_COUNT = 3

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s::%(funcName)s() (%(lineno)s)]: %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'verbose'
        },
        'file_django': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django', 'console'],
            'propagate': True,
            'level': 'ERROR',
        },
        'website': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'openkamer': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'wikidata': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'scraper': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'parliament': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'government': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'document': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'gift': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'person': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'stats': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'oktwitter': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django_cron': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'tkapi': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}
