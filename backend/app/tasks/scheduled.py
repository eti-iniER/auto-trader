import logging

import dramatiq
from periodiq import cron

logger = logging.getLogger(__name__)

MIDNIGHT_ON_SUNDAYS = cron("0 0 * * 0")


@dramatiq.actor(periodic=MIDNIGHT_ON_SUNDAYS)
async def poll_scheduled_tasks():
    pass
