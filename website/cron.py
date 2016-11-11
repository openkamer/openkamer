import logging
import os
import traceback
import datetime

from django.conf import settings
from django_cron import CronJobBase, Schedule

from git import Repo, Actor

import scraper.political_parties
import scraper.parliament_members

from website import settings

logger = logging.getLogger(__name__)


class CreateCommitPartyCSV(CronJobBase):
    RUN_AT_TIMES = ['19:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.CreateCommitPartyCSV'

    def do(self):
        logger.info('BEGIN')
        try:
            repo = Repo(settings.PARTIES_REPO_DIR)
            assert not repo.bare
            # origin = repo.create_remote('origin', repo.remotes.origin.url)
            # origin.pull()

            parties = scraper.political_parties.search_parties()
            filepath = os.path.join(settings.PARTIES_REPO_DIR, 'fracties.csv')
            scraper.political_parties.create_parties_csv(parties, filepath)
            changed_files = repo.git.diff(name_only=True)

            if not changed_files:
                logger.info('no changes')
                logger.info('END')
                return

            filepath_date = os.path.join(settings.PARTIES_REPO_DIR, 'date.txt')
            with open(filepath_date, 'w') as fileout:
                fileout.write(datetime.date.today().strftime('%Y-%m-%d'))

            index = repo.index
            index.add(['fracties.csv', 'date.txt'])
            author = Actor(settings.GIT_AUTHOR_NAME, settings.GIT_AUTHOR_EMAIL)
            index.commit(
                message='update of tweedekamer.nl fracties',
                author=author
            )
            # origin.push()
        except:
            logger.error(traceback.format_exc())
            raise
        logger.info('END')


class CreateCommitParliamentMembersCSV(CronJobBase):
    RUN_AT_TIMES = ['19:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.CreateCommitParliamentMembersCSV'

    def do(self):
        logger.info('BEGIN')
        try:
            repo = Repo(settings.MEMBERS_REPO_DIR)
            assert not repo.bare
            # origin = repo.create_remote('origin', repo.remotes.origin.url)
            # origin.pull()

            parties = scraper.parliament_members.search_members()
            filepath = os.path.join(settings.MEMBERS_REPO_DIR, 'tweedekamerleden.csv')
            scraper.parliament_members.create_members_csv(parties, filepath)
            changed_files = repo.git.diff(name_only=True)

            if not changed_files:
                logger.info('no changes')
                logger.info('END')
                return

            filepath_date = os.path.join(settings.MEMBERS_REPO_DIR, 'date.txt')
            with open(filepath_date, 'w') as fileout:
                fileout.write(datetime.date.today().strftime('%Y-%m-%d'))

            index = repo.index
            index.add(['tweedekamerleden.csv', 'date.txt'])
            author = Actor(settings.GIT_AUTHOR_NAME, settings.GIT_AUTHOR_EMAIL)
            index.commit(
                message='update of tweedekamer.nl kamerleden',
                author=author
            )
            # origin.push()
        except:
            logger.error(traceback.format_exc())
            raise
        logger.info('END')
