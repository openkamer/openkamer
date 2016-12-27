import logging

from django_cron import CronJobBase, Schedule

import stats.models

logger = logging.getLogger(__name__)


class UpdateStatsData(CronJobBase):
    RUN_AT_TIMES = ['06:00']
    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'stats.cron.UpdateStatsData'

    def do(self):
        logger.info('BEGIN')
        try:
            stats.models.update_all()
        except Exception as error:
            logger.exception(error)
            raise
        logger.info('END')
