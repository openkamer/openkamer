import csv
import datetime
import gzip
import logging
import os
import shutil
import time

import fasteners

from django.core import management
from django.conf import settings
from django.core.paginator import Paginator
from django_cron import CronJobBase, Schedule
from django.db import transaction
from django.db.utils import IntegrityError

from document.models import Kamervraag
from document.models import Submitter
from document.util import years_from_str_list
from government.models import GovernmentMember
from parliament.models import PartyMember
from parliament.models import ParliamentMember
from person.models import Person
from person.views import PersonTKIDCheckView

import openkamer.dossier
import openkamer.gift
import openkamer.kamervraag
import openkamer.parliament
import openkamer.travel
import openkamer.verslagao

import stats.models

from website import settings

logger = logging.getLogger(__name__)


class LockJob(CronJobBase):
    """
    django-cron does provide a file lock backend,
    but this is not working due to issue https://github.com/Tivix/django-cron/issues/74
    """
    code = None

    def do(self):
        logger.info('BEGIN: {}'.format(self.code))
        lockfilepath = os.path.join(settings.CRON_LOCK_DIR, 'tmp_{}_lockfile'.format(self.code))
        a_lock = fasteners.InterProcessLock(lockfilepath)
        gotten = a_lock.acquire(timeout=1.0)
        try:
            if gotten:
                self.do_imp()
            else:
                logger.info('Not able to acquire lock, job is already running')
        finally:
            if gotten:
                a_lock.release()
        logger.info('END: {}'.format(self.code))

    def do_imp(self):
        raise NotImplementedError


class TestJob(LockJob):
    RUN_EVERY_MINS = 0
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'website.cron.TestJob'

    def do_imp(self):
        logger.info('BEGIN')
        time.sleep(10)
        logger.info('END')


class UpdateParliamentAndGovernment(LockJob):
    RUN_AT_TIMES = ['20:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateParliamentAndGovernment'

    def do_imp(self):
        logger.info('BEGIN')
        try:
            openkamer.parliament.create_parliament_and_government()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')


class UpdateActiveDossiers(LockJob):
    RUN_AT_TIMES = ['21:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateActiveDossiers'

    def do_imp(self):
        # TODO: also update dossiers that have closed since last update
        logger.info('update active dossiers cronjob')
        failed_dossiers = openkamer.dossier.create_wetsvoorstellen_active()
        if failed_dossiers:
            logger.error('the following dossiers failed: ' + str(failed_dossiers))


class UpdateInactiveDossiers(LockJob):
    RUN_AT_TIMES = ['12:00']  # note that while it runs every day, it only updates a set depending on the week day
    DAYS_PER_WEEK = 7
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateInactiveDossiers'

    def do_imp(self):
        logger.info('update inactive dossiers cronjob')
        week_day = datetime.date.today().weekday()
        try:
            years = years_from_str_list(2008)
            for year in years:
                year = int(year)
                if year % self.DAYS_PER_WEEK == week_day:
                    logger.info('year: {}'.format(year))
                    failed_dossiers = openkamer.dossier.create_wetsvoorstellen_inactive(year=year)
                    if failed_dossiers:
                        logger.error('the following dossiers failed: {}'.format(failed_dossiers))
        except:
            logger.exception('something failed')


class UpdateVerslagenAlgemeenOverleg(LockJob):
    RUN_AT_TIMES = ['23:30']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateVerslagenAlgemeenOverleg'

    def do_imp(self):
        logger.info('update verslagen algemeen overleg')
        skip_if_exists = datetime.date.today().day % 7 == 0
        years = years_from_str_list(2008)
        for year in years:
            openkamer.verslagao.create_verslagen_algemeen_overleg(year, max_n=None, skip_if_exists=skip_if_exists)


class UpdateKamervragenRecent(LockJob):
    RUN_AT_TIMES = ['00:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateKamervragenRecent'

    def do_imp(self):
        logger.info('update kamervragen and kamerantwoorden')
        years = years_from_str_list(2019)
        for year in years:
            openkamer.kamervraag.create_kamervragen(year, skip_if_exists=False)


class UpdateKamervragenAll(LockJob):
    RUN_EVERY_MINS = 60 * 24 * 7  # 7 days
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'website.cron.UpdateKamervragenAll'

    def do_imp(self):
        logger.info('update kamervragen and kamerantwoorden')
        years = years_from_str_list(2010)
        for year in years:
            openkamer.kamervraag.create_kamervragen(year, skip_if_exists=False)


class UpdateSubmitters(LockJob):
    RUN_AT_TIMES = ['05:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateSubmitters'

    def do_imp(self):
        logger.info('BEGIN')
        BATCH_SIZE = 100
        try:
            submitters = Submitter.objects.all().order_by('party_slug')
            paginator = Paginator(submitters, BATCH_SIZE)
            logger.info('{} submitters to update'.format(paginator.count))
            for page in paginator.page_range:
                progress_percent = int(page / paginator.num_pages * 100)
                logger.info('{}%'.format(progress_percent))
                submitters = paginator.get_page(page)
                try:
                    self.update_batch(submitters)
                except IntegrityError as e:
                    logger.exception('Error updating batch submitters at page {}, skipping batch'.format(page))
                    continue
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')

    @transaction.atomic
    def update_batch(self, submitters):
        for submitter in submitters:
            submitter.update_submitter_party_slug()


class UpdateSearchIndex(LockJob):
    RUN_AT_TIMES = ['06:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateSearchIndex'

    def do_imp(self):
        logger.info('BEGIN')
        try:
            management.call_command('rebuild_index', '--noinput')
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')


class UpdateStatsData(LockJob):
    RUN_AT_TIMES = ['07:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateStatsData'

    def do_imp(self):
        logger.info('BEGIN')
        try:
            stats.models.update_all()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')


class UpdateGifts(LockJob):
    RUN_AT_TIMES = ['12:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateGifts'

    def do_imp(self):
        logger.info('BEGIN')
        try:
            openkamer.gift.create_gifts()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')


class UpdateTravels(LockJob):
    RUN_AT_TIMES = ['14:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.UpdateTravels'

    def do_imp(self):
        logger.info('BEGIN')
        try:
            openkamer.travel.create_travels()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')


class CleanUnusedPersons(CronJobBase):
    RUN_AT_TIMES = ['08:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.CleanUnusedPersons'

    def do(self):
        logger.info('run unused persons cleanup')
        persons = Person.objects.all()
        persons_to_delete_ids = []
        for person in persons:
            members = PartyMember.objects.filter(person=person)
            if members:
                continue
            members = ParliamentMember.objects.filter(person=person)
            if members:
                continue
            members = GovernmentMember.objects.filter(person=person)
            if members:
                continue
            submitters = Submitter.objects.filter(person=person)
            if submitters:
                continue
            persons_to_delete_ids.append(person.id)
        Person.objects.filter(id__in=persons_to_delete_ids).delete()
        logger.info('deleted persons: ' + str(persons_to_delete_ids))
        logger.info('END')


class MergeDuplicatePersons(CronJobBase):
    RUN_AT_TIMES = ['08:15']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.MergeDuplicatePersons'

    def do(self):
        logger.info('run merge duplicate persons')
        tk_ids = PersonTKIDCheckView.get_duplicate_person_tk_ids()
        logger.info('duplicate ids: {}'.format(tk_ids))
        try:
            for tk_id in tk_ids:
                persons = Person.objects.filter(tk_id=tk_id)
                self.try_merge_persons(persons)
        except Exception as e:
            logger.exception('Error merging duplicated persons')
            raise
        logger.info('END')

    @staticmethod
    def try_merge_persons(persons):
        for person in persons:
            logger.info('===============')
            logger.info('person: {}'.format(person))
            if not person.surname or not person.initials:
                continue
            person_best = Person.find_surname_initials(person.surname, person.initials, persons)
            persons_delete = persons.exclude(id=person_best.id)
            logger.info('best {}, delete: {}'.format(person_best, persons_delete))
            submitters = Submitter.objects.filter(person__in=persons_delete)
            for submitter in submitters:
                if Submitter.objects.filter(person=person_best, document=submitter.document).exists():
                    continue
                submitter.person = person_best
                submitter.update_submitter_party_slug()
                submitter.save()
            persons_delete.delete()
            break


class BackupDaily(LockJob):
    RUN_AT_TIMES = ['18:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.BackupDaily'

    def do_imp(self):
        logger.info('run daily backup cronjob')
        BackupDaily.remove_old_json_dumps(days_old=settings.JSON_DUMP_KEEP_DAYS)
        management.call_command('dbbackup', '--clean')
        try:
            BackupDaily.create_json_dump()
        except Exception as e:
            logger.exception(e)
            raise

    @staticmethod
    def create_json_dump():
        filepath = os.path.join(settings.DBBACKUP_STORAGE_OPTIONS['location'], 'openkamer-{}.json'.format(datetime.date.today()))
        filepath_compressed = filepath + '.gz'
        with open(filepath, 'w') as fileout:
            management.call_command(
                'dumpdata',
                '--all',
                '--natural-foreign',
                '--exclude', 'auth.permission',
                '--exclude', 'contenttypes',
                'person',
                'parliament',
                'government',
                'document',
                'gift',
                'travel',
                'stats',
                'website',
                stdout=fileout
            )
        with open(filepath, 'rb') as f_in:
            with gzip.open(filepath_compressed, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(filepath)

    @staticmethod
    def remove_old_json_dumps(days_old):
        for (dirpath, dirnames, filenames) in os.walk(settings.DBBACKUP_STORAGE_OPTIONS['location']):
            for file in filenames:
                if '.json' not in file:
                    continue
                filepath = os.path.join(dirpath, file)
                datetime_created = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
                if datetime_created < datetime.datetime.now() - datetime.timedelta(days=days_old):
                    os.remove(filepath)


class CreateCSVExports(LockJob):
    RUN_AT_TIMES = ['18:15']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'website.cron.CreateCSVExports'

    def do_imp(self):
        logger.info('run daily csv export job')
        try:
            self.create_kamervragen_csv_exports()
        except Exception as e:
            logger.exception(e)
            raise

    @staticmethod
    def create_kamervragen_csv_exports():
        years = years_from_str_list(2008)
        for year in years:
            logger.info('create year {}'.format(year))
            year = int(year)
            year_begin = datetime.date(year=year, month=1, day=1)
            year_end = datetime.date(year=year + 1, month=1, day=1)
            kamervragen = Kamervraag.objects.filter(document__date_published__gte=year_begin, document__date_published__lt=year_end).order_by('document__date_published')
            filepath = os.path.join(settings.CSV_EXPORT_PATH, 'openkamer_kamervragen_{}.csv'.format(year))
            with open(filepath, 'w') as csvfile:
                filewriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                headers = ['vraagnummer', 'datum', 'ministeries', 'ontvangers', 'titel']
                filewriter.writerow(headers)
                for kamervraag in kamervragen:
                    ministries = []
                    for receiver in kamervraag.document.receivers:
                        for member in receiver.government_members:
                            if member.position.ministry:
                                ministries.append(member.position.ministry.name)
                    receivers = [receiver.person.fullname() for receiver in kamervraag.document.receivers]
                    row = [
                        kamervraag.vraagnummer,
                        str(kamervraag.document.date_published),
                        ';'.join(ministries),
                        ';'.join(receivers),
                        kamervraag.document.title_short,
                    ]
                    filewriter.writerow(row)
