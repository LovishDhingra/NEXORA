from django.contrib import admin

from .models import AuditLog, DomainEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id")
    list_filter = ("action", "entity_type")


@admin.register(DomainEvent)
class DomainEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "event_type", "published_at")
