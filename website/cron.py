import logging
import os
import traceback
import datetime

from django.conf import settings
from django_cron import CronJobBase, Schedule

from git import Repo, Actor

import scraper.dossiers
import scraper.documents
import scraper.political_parties
import scraper.parliament_members

from website import settings

logger = logging.getLogger(__name__)


class CreateCommitWetsvoorstellenIDs(CronJobBase):
    RUN_AT_TIMES = ['20:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.CreateCommitWetsvoorstellenIDs'

    @staticmethod
    def dossier_ids_to_file(dossier_ids, filepath):
        dossier_ids = sorted(dossier_ids)
        with open(filepath, 'w') as fileout:
            for dossier_id in dossier_ids:
                fileout.write(dossier_id + '\n')

    def do(self):
        logger.info('BEGIN')
        try:
            repo = Repo(settings.WETSVOORSTELLEN_REPO_DIR)
            assert not repo.bare
            # origin = repo.create_remote('origin', repo.remotes.origin.url)
            # origin.pull()

            filename_iaan = 'wetsvoorstellen_dossier_ids_initiatief_aanhangig.txt'
            filepath = os.path.join(settings.WETSVOORSTELLEN_REPO_DIR, filename_iaan)
            dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_initiatief(filter_active=True)
            assert len(dossier_ids) > 105
            self.dossier_ids_to_file(dossier_ids, filepath)

            filename_iaf = 'wetsvoorstellen_dossier_ids_initiatief_afgedaan.txt'
            filepath = os.path.join(settings.WETSVOORSTELLEN_REPO_DIR, filename_iaf)
            dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_initiatief(filter_inactive=True)
            assert len(dossier_ids) > 68
            self.dossier_ids_to_file(dossier_ids, filepath)

            filename_raan = 'wetsvoorstellen_dossier_ids_regering_aanhangig.txt'
            filepath = os.path.join(settings.WETSVOORSTELLEN_REPO_DIR, filename_raan)
            dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_regering(filter_active=True)
            assert len(dossier_ids) > 120
            self.dossier_ids_to_file(dossier_ids, filepath)

            filename_raf = 'wetsvoorstellen_dossier_ids_regering_afgedaan.txt'
            filepath = os.path.join(settings.WETSVOORSTELLEN_REPO_DIR, filename_raf)
            dossier_ids = scraper.dossiers.get_dossier_ids_wetsvoorstellen_regering(filter_inactive=True)
            assert len(dossier_ids) > 1266
            self.dossier_ids_to_file(dossier_ids, filepath)

            changed_files = repo.git.diff(name_only=True)
            if not changed_files:
                logger.info('no changes')
                logger.info('END')
                return

            filepath_date = os.path.join(settings.WETSVOORSTELLEN_REPO_DIR, 'date.txt')
            with open(filepath_date, 'w') as fileout:
                fileout.write(datetime.date.today().strftime('%Y-%m-%d'))

            index = repo.index
            index.add([filename_iaan, filename_iaf, filename_raan, filename_raf, 'date.txt'])
            author = Actor(settings.GIT_AUTHOR_NAME, settings.GIT_AUTHOR_EMAIL)
            index.commit(
                message='update of wetsvoorstellen dossier ids',
                author=author
            )
            # origin.push()
        except:
            logger.error(traceback.format_exc())
            raise
        logger.info('END')


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
