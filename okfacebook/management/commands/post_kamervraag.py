from django.core.management.base import BaseCommand

import okfacebook.kamervraag


class Command(BaseCommand):

    def handle(self, *args, **options):
        okfacebook.kamervraag.post_kamervraag()
