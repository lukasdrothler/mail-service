from src.rmq_consumer import RabbitMQConsumer
from src.mail_service import MailService

import logging, os

from dotenv import load_dotenv

load_dotenv()
is_dev = False

try:
    if os.getenv('CURRENT_ENV') == 'development':
        is_dev = True
except KeyError:
    pass

if is_dev:
    log_level = logging.INFO
else:
    log_level = logging.WARNING

logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)

if __name__ == '__main__':
    mail_service = MailService()
    consumer = RabbitMQConsumer(mail_service)
    consumer.start()
