from django.core.management.base import BaseCommand

import oktwitter.lists


class Command(BaseCommand):

    def handle(self, *args, **options):
        oktwitter.lists.update_current_government_members_list()
