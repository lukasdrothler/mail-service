import pytest
import os
from src.mail_service import MailService
from src.rmq_consumer import RabbitMQConsumer
from testcontainers.rabbitmq import RabbitMqContainer

@pytest.fixture(scope="function")
def mail_service():
    """Fixture for MailService with mocked environment variables."""
    old_environ = os.environ.copy()
    os.environ.update({
        "SMTP_SERVER": "localhost",
        "SMTP_PORT": "587",
        "SMTP_USER": "test_user",
        "SMTP_PASSWORD": "test_password",
        "APP_NAME": "TestApp",
        "APP_OWNER": "TestOwner",
        "CONTACT_EMAIL": "test@example.com"
    })
    try:
        return MailService()
    finally:
        os.environ.clear()
        os.environ.update(old_environ)

@pytest.fixture(scope="session")
def rabbitmq_server():
    """Fixture to provide a RabbitMQ server (container or existing)."""
    if os.getenv("RABBITMQ_HOST"):
        yield None
    else:
        with RabbitMqContainer("rabbitmq:4.2") as rabbitmq:
            yield rabbitmq

@pytest.fixture(scope="function")
def rmq_consumer(mail_service, rabbitmq_server):
    """Fixture for RabbitMQConsumer with real connection."""
    env_vars = {}

    if rabbitmq_server:
        env_vars = {
            "RABBITMQ_HOST": rabbitmq_server.get_container_host_ip(),
            "RABBITMQ_PORT": str(rabbitmq_server.get_exposed_port(5672)),
            "RABBITMQ_MAIL_QUEUE_NAME": "test_queue",
            "RABBITMQ_USERNAME": "guest",
            "RABBITMQ_PASSWORD": "guest"
        }
    else:
        # Fallback defaults if not provided by environment
        if "RABBITMQ_MAIL_QUEUE_NAME" not in os.environ:
            env_vars["RABBITMQ_MAIL_QUEUE_NAME"] = "test_queue"
        if "RABBITMQ_USERNAME" not in os.environ:
            env_vars["RABBITMQ_USERNAME"] = "test_user"
        if "RABBITMQ_PASSWORD" not in os.environ:
            env_vars["RABBITMQ_PASSWORD"] = "test_password"
    
    old_environ = os.environ.copy()
    os.environ.update(env_vars)
    try:
        return RabbitMQConsumer(mail_service, dry_run=True)
    finally:
        os.environ.clear()
        os.environ.update(old_environ)
