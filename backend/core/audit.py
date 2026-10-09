from .models import AuditLog


def record(action: str, entity_type: str, entity_id, **details) -> AuditLog:
    return AuditLog.objects.create(
        action=action, entity_type=entity_type, entity_id=str(entity_id), details=details
    )
