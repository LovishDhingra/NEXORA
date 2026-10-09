from django.contrib import admin

from .models import CreditApplication, Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "credit_score")


@admin.register(CreditApplication)
class CreditApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "credit_score", "card_type", "created_at")
    list_filter = ("status", "card_type")
