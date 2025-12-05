def test_rabbitmq_connection(rmq_consumer):
    """Test that the RabbitMQ consumer connects successfully."""
    assert rmq_consumer is not None
    assert rmq_consumer.host is not None
