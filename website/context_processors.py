from website import __version__
from website import settings


def version(request):
    return {'openkamer_version': __version__}


def piwik(request):
    return {
        'piwik_url': settings.PIWIK_URL,
        'piwik_site_id': settings.PIWIK_SITE_ID
    }
