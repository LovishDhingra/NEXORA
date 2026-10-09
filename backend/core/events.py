"""Tiny event bus: persist to an outbox table, then try Kafka if configured."""
import json
import logging

from django.conf import settings
from django.utils import timezone

from .models import DomainEvent

log = logging.getLogger(__name__)


def publish(event_type: str, **payload) -> DomainEvent:
    event = DomainEvent.objects.create(event_type=event_type, payload=payload)
    if settings.KAFKA_BOOTSTRAP_SERVERS:
        try:
            from kafka import KafkaProducer  # optional dependency

            producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            producer.send(settings.KAFKA_TOPIC, {"type": event_type, **payload})
            producer.flush(timeout=5)
            event.published_at = timezone.now()
            event.save(update_fields=["published_at"])
        except Exception:  # never let messaging break the business flow
            log.exception("Kafka publish failed for %s; event kept in outbox", event_type)
    return event
