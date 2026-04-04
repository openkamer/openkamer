import logging
import time

logger = logging.getLogger('website.request')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        user = getattr(request, 'user', None)
        username = user.get_username() if user and user.is_authenticated else '-'
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '-'))

        logger.info(
            '%s %s %s %s %s %dms',
            ip,
            username,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )
        return response
