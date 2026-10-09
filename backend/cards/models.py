from django.db import models


class CardType(models.TextChoices):
    PLATINUM = "PLATINUM", "Platinum"
    GOLD = "GOLD", "Gold"
    VISA = "VISA", "Visa"


class CreditCard(models.Model):
    application = models.OneToOneField("applications.CreditApplication", on_delete=models.PROTECT, related_name="card")
    customer = models.ForeignKey("applications.Customer", on_delete=models.PROTECT, related_name="cards")
    card_number = models.CharField(max_length=16, unique=True)
    card_type = models.CharField(max_length=16, choices=CardType.choices)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2)
    expires_on = models.DateField()

    pin_hash = models.CharField(max_length=128)  # never store the PIN itself
    pin_is_default = models.BooleanField(default=True)
    failed_pin_attempts = models.PositiveSmallIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    pin_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def masked_number(self):
        return f"•••• •••• •••• {self.card_number[-4:]}"

    def __str__(self):
        return f"{self.card_type} {self.masked_number}"
