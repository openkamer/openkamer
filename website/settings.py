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
    'website.middleware.RequestLoggingMiddleware',
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
LOGFILE_MAXSIZE = 10 * 1024 * 1024  # 10 MB

# Number of old log files that are stored before they are deleted
# see https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler
LOGFILE_BACKUP_COUNT = 3

# Project app names that share the standard DEBUG handler set
_APP_LOGGER_NAMES = [
    'website', 'openkamer', 'wikidata', 'scraper', 'parliament',
    'government', 'document', 'gift', 'travel', 'person', 'stats',
    'oktwitter', 'django_cron',
]

LOGGING = {
    'version': 1,
    # Keep loggers configured by third-party libraries intact
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname:<8} [{name}::{funcName}() ({lineno})]: {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'access': {
            # Compact format for the per-request access log
            'format': '[{asctime}] {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'verbose',
        },
        'file_django': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'error.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'debug.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
        'file_requests': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'requests.log'),
            'maxBytes': LOGFILE_MAXSIZE,
            'backupCount': LOGFILE_BACKUP_COUNT,
            'encoding': 'utf-8',
            'formatter': 'access',
        },
    },
    'loggers': {
        # Catch-all: surface warnings from any third-party library not listed below.
        # file_debug accepts WARNING+; file_error accepts ERROR+ — both get the right subset.
        '': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Django framework errors → both django.log and error.log so error.log is complete
        'django': {
            'handlers': ['file_django', 'file_error', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # 4xx → WARNING (only reaches file_debug); 5xx → ERROR (reaches both files)
        'django.request': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Keep SQL noise off the files; add file_error so DB errors survive in production
        'django.db.backends': {
            'handlers': ['file_error', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Per-request access log
        'website.request': {
            'handlers': ['file_requests', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Third-party API client — INFO and above only
        'tkapi': {
            'handlers': ['file_debug', 'file_error', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # All project apps — full DEBUG logging
        **{
            name: {
                'handlers': ['file_debug', 'file_error', 'console'],
                'level': 'DEBUG',
                'propagate': False,
            }
            for name in _APP_LOGGER_NAMES
        },
    },
}
