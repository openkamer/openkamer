import datetime
import logging

from django_cron import CronJobBase, Schedule

import oktwitter.lists

logger = logging.getLogger(__name__)


class UpdateTwitterLists(CronJobBase):
    RUN_AT_TIMES = ['06:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'oktwitter.cron.UpdateTwitterLists'

    def do(self):
        logger.info('BEGIN')
        try:
            oktwitter.lists.update_current_government_members_list()
            oktwitter.lists.update_current_parliament_members_list()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')
