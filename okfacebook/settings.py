from django.conf import settings

FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', '')
FACEBOOK_API_PAGE_TOKEN = getattr(settings, 'FACEBOOK_API_PAGE_TOKEN', '')  # use manage.py get_login_token <short-lived-page-token> to get a long lived token
FACEBOOK_PROFLE_ID = getattr(settings, 'FACEBOOK_PROFLE_ID', '')
