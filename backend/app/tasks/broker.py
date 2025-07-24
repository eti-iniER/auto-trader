import logging

import dramatiq
from app.config import settings
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO
from periodiq import PeriodiqMiddleware

broker = RabbitmqBroker(url=settings.DRAMATIQ_BROKER_URL)
broker.add_middleware(AsyncIO())
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))


dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

from app.tasks.scheduled import *
