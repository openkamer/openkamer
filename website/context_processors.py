from website import settings


def piwik(request):
    return {
        'piwik_url': settings.PIWIK_URL,
        'piwik_site_id': settings.PIWIK_SITE_ID
    }
