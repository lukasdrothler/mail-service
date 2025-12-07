import pytest
import json
import pika
import threading
import time
from src.basemodels import BrandingConfig, TemplateName

def test_consume_all_templates(rmq_consumer, rabbitmq_server):
    # Start consumer in a thread
    consumer_thread = threading.Thread(target=rmq_consumer.start, daemon=True)
    consumer_thread.start()
    
    # Give it a moment to start consuming
    time.sleep(2)
    
    # Setup connection for publishing
    credentials = pika.PlainCredentials(rmq_consumer.username, rmq_consumer.password)
    parameters = pika.ConnectionParameters(
        host=rmq_consumer.host,
        port=rmq_consumer.port,
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    branding_config = BrandingConfig(
        app_name="TestApp",
        app_owner="TestOwner",
        contact_email="support@testapp.com"
    )
    
    # 1. Email Verification
    content_ver = {"username": "User1", "verification_code": "111111"}
    req_ver = {
        "template_name": TemplateName.EMAIL_VERIFICATION,
        "username": "User1",
        "verification_code": "111111",
        "recipient": "user1@example.com",
        "branding_config": branding_config.model_dump(),
        "email_content": content_ver
    }
    channel.basic_publish(
        exchange='',
        routing_key=rmq_consumer.mail_queue_name,
        body=json.dumps(req_ver)
    )
    
    # 2. Email Change Verification
    content_change = {"username": "User2", "verification_code": "222222"}
    req_change = {
        "template_name": TemplateName.EMAIL_CHANGE_VERIFICATION,
        "username": "User2",
        "verification_code": "222222",
        "recipient": "user2@example.com",
        "branding_config": branding_config.model_dump(),
        "email_content": content_change
    }
    channel.basic_publish(
        exchange='',
        routing_key=rmq_consumer.mail_queue_name,
        body=json.dumps(req_change)
    )
    
    # 3. Forgot Password Verification
    content_forgot = {"username": "User3", "verification_code": "333333"}
    req_forgot = {
        "template_name": TemplateName.FORGOT_PASSWORD_VERIFICATION,
        "username": "User3",
        "verification_code": "333333",
        "recipient": "user3@example.com",
        "branding_config": branding_config.model_dump(),
        "email_content": content_forgot
    }
    channel.basic_publish(
        exchange='',
        routing_key=rmq_consumer.mail_queue_name,
        body=json.dumps(req_forgot)
    )
    
    # Wait for processing
    time.sleep(2)
    
    # Verify queue is empty (messages consumed)
    queue_state = channel.queue_declare(queue=rmq_consumer.mail_queue_name, passive=True)
    assert queue_state.method.message_count == 0
    
    connection.close()
    
    # Stop consumer
    rmq_consumer.stop()
    consumer_thread.join()

def test_consume_invalid_request_dlq(rmq_consumer, rabbitmq_server):
    # Start consumer in a thread
    consumer_thread = threading.Thread(target=rmq_consumer.start, daemon=True)
    consumer_thread.start()
    
    # Give it a moment to start consuming
    time.sleep(2)
    
    # Setup connection for publishing
    credentials = pika.PlainCredentials(rmq_consumer.username, rmq_consumer.password)
    parameters = pika.ConnectionParameters(
        host=rmq_consumer.host,
        port=rmq_consumer.port,
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    # Purge DLQ to ensure clean state
    dlq_name = f"{rmq_consumer.mail_queue_name}_dlq"
    channel.queue_purge(queue=dlq_name)
    
    # Publish invalid message (invalid JSON)
    invalid_message = "This is not a valid JSON"
    channel.basic_publish(
        exchange='',
        routing_key=rmq_consumer.mail_queue_name,
        body=invalid_message
    )
    
    # Wait for processing
    time.sleep(2)
    
    # Verify main queue is empty
    queue_state = channel.queue_declare(queue=rmq_consumer.mail_queue_name, passive=True)
    assert queue_state.method.message_count == 0
    
    # Verify DLQ has the message
    dlq_state = channel.queue_declare(queue=dlq_name, passive=True)
    assert dlq_state.method.message_count == 1
    
    connection.close()
    
    # Stop consumer
    rmq_consumer.stop()
    consumer_thread.join()
