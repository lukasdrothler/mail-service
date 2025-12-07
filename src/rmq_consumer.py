import pika, os, json, time, logging, socket

from src.basemodels import MailRequest, TemplateName
from src.mail_service import MailService

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, mail_service: MailService, dry_run: bool = False):
        if "RABBITMQ_HOST" in os.environ:
            self.host = os.environ["RABBITMQ_HOST"]
        else:
            self.host = "localhost"
        
        # Resolve and log IP for debugging
        try:
            resolved_ip = socket.gethostbyname(self.host)
            logger.info(f"RabbitMQ host set to: {self.host} (Resolved IP: {resolved_ip})")
        except Exception as e:
            logger.error(f"Failed to resolve RabbitMQ host {self.host}: {e}")
            resolved_ip = "unknown"

        if "RABBITMQ_PORT" in os.environ:
            self.port = int(os.environ["RABBITMQ_PORT"])
        else:
            self.port = 5672
        logger.info(f"RabbitMQ port set to: {self.port}")

        if "RABBITMQ_MAIL_QUEUE_NAME" in os.environ:
            self.mail_queue_name = os.environ["RABBITMQ_MAIL_QUEUE_NAME"]
            logger.info(f"RabbitMQ queue name set from env: {self.mail_queue_name}")
        else:
            raise ValueError("RABBITMQ_MAIL_QUEUE_NAME environment variable is required")

        if "RABBITMQ_USERNAME" in os.environ:
            self.username = os.environ["RABBITMQ_USERNAME"]
            logger.info(f"RabbitMQ username set to: {self.username}")
        else:
            raise ValueError("RABBITMQ_USERNAME environment variable is required")
        
        if "RABBITMQ_PASSWORD" in os.environ:
            self.password = os.environ["RABBITMQ_PASSWORD"]
            logger.info(f"RabbitMQ password set from env")
        else:
            raise ValueError("RABBITMQ_PASSWORD environment variable is required")
        
        self.mail_service = mail_service
        self.dry_run = dry_run

        # Connect to RabbitMQ with retry logic
        self._connection = self._connect_with_retry()

        self._channel = self._connection.channel()
        
        # Setup Dead Letter Exchange (DLX) and Queue (DLQ)
        dlx_name = f"{self.mail_queue_name}_dlx"
        dlq_name = f"{self.mail_queue_name}_dlq"
        
        # Declare DLX (Fanout type broadcasts to all bound queues)
        self._channel.exchange_declare(exchange=dlx_name, exchange_type='fanout', durable=True)
        
        # Declare DLQ
        self._channel.queue_declare(queue=dlq_name, durable=True)
        
        # Bind DLQ to DLX
        self._channel.queue_bind(exchange=dlx_name, queue=dlq_name)
        
        # Declare main queue with DLX configuration
        # Messages rejected with requeue=False will be sent to the DLX
        queue_args = {
            'x-dead-letter-exchange': dlx_name
        }
        
        self._channel.queue_declare(queue=self.mail_queue_name, durable=True, arguments=queue_args)
        self._channel.basic_qos(prefetch_count=1)

    def start(self):
        self._channel.basic_consume(
            queue=self.mail_queue_name, 
            on_message_callback=self.callback
            )
        
        logger.info('Waiting for messages...')
        self._channel.start_consuming()

    def stop(self):
        """Stop the consumer gracefully"""
        if self._connection and self._connection.is_open:
            logger.info("Stopping consumer...")
            self._connection.add_callback_threadsafe(self._channel.stop_consuming)

    def _connect_with_retry(self, max_retries=10, retry_delay=5):
        """Connect to RabbitMQ with retry logic for container startup"""
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port} (attempt {attempt + 1}/{max_retries})")
                connection = pika.BlockingConnection(parameters)
                logger.info(f"Successfully connected to RabbitMQ")
                return connection
            except pika.exceptions.AMQPConnectionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts")
                    raise


    @staticmethod
    def request_json_to_dict(json_data) -> MailRequest:
        data = json.loads(json_data.decode())
        return MailRequest(**data)


    def handle_request(self, request: MailRequest):
        # Placeholder for handling the mail sending logic
        logger.info(f"Handling mail request for {request.recipient} using template {request.template_name}")
        logger.info(f"Request details: {request}")

        if request.template_name in [
            TemplateName.EMAIL_VERIFICATION,
            TemplateName.EMAIL_CHANGE_VERIFICATION,
            TemplateName.FORGOT_PASSWORD_VERIFICATION
        ]:
            self.mail_service.send_code_mail(request, request.template_name)
        else:
            self.mail_service.send_custom_template_mail(request, request.template_name)


    def callback(self, ch, method, properties, body):
        try:
            logger.info(f"Received message: {method.delivery_tag}")
            request = self.request_json_to_dict(body)
            self.handle_request(request)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed message: {method.delivery_tag}")
        except Exception as e:
            logger.error(f"Error processing message {method.delivery_tag}: {e}")
            # Rejecting with requeue=False sends the message to the configured Dead Letter Exchange (DLX)
            # This prevents infinite loops for bad messages while preserving them in the DLQ for inspection
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            logger.warning(f"Message {method.delivery_tag} sent to Dead Letter Queue")