from django.db import models


class AuditLog(models.Model):
    """Append-only trail of business actions (never stores PINs or full card numbers)."""

    action = models.CharField(max_length=64, db_index=True)
    entity_type = models.CharField(max_length=32)
    entity_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} {self.entity_type}#{self.entity_id}"


class DomainEvent(models.Model):
    """Outbox table. Events are stored here and optionally forwarded to Kafka."""

    event_type = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.event_type
