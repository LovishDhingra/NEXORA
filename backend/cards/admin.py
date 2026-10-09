from django.contrib import admin

from .models import CreditCard


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ("masked_number", "card_type", "credit_limit", "pin_is_default", "is_locked")
    exclude = ("pin_hash",)
