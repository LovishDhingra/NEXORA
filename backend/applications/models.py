from django.db import models


class IdDocumentType(models.TextChoices):
    PASSPORT = "PASSPORT", "Passport"
    NATIONAL_ID = "NATIONAL_ID", "National ID"
    DRIVING_LICENSE = "DRIVING_LICENSE", "Driving licence"
    SSN = "SSN", "Social security number"


class EmploymentType(models.TextChoices):
    SALARIED = "SALARIED", "Salaried"
    SELF_EMPLOYED = "SELF_EMPLOYED", "Self-employed"


class Customer(models.Model):
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    date_of_birth = models.DateField()
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    employment_type = models.CharField(max_length=16, choices=EmploymentType.choices)
    employer_name = models.CharField(max_length=120)
    job_title = models.CharField(max_length=120)
    annual_salary = models.DecimalField(max_digits=12, decimal_places=2)  # USD
    existing_credit_cards = models.PositiveSmallIntegerField(default=0)  # self-declared, at other banks

    id_document_type = models.CharField(max_length=20, choices=IdDocumentType.choices)
    id_document_number = models.CharField(max_length=24)  # stored normalised (upper-case, no spaces)

    credit_score = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["id_document_type", "id_document_number"], name="uniq_customer_identity")
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CardNetwork(models.TextChoices):
    VISA = "VISA", "Visa"
    MASTERCARD = "MASTERCARD", "Mastercard"
    AMEX = "AMEX", "American Express"
    RUPAY = "RUPAY", "RuPay"
    OTHER = "OTHER", "Other"


class ExistingCard(models.Model):
    """A card the applicant says they hold at another bank."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="other_cards")
    issuer = models.CharField(max_length=60)
    network = models.CharField(max_length=12, choices=CardNetwork.choices)

    def __str__(self):
        return f"{self.issuer} {self.get_network_display()}"


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    DOCUMENTS_REQUESTED = "DOCUMENTS_REQUESTED", "Additional documents requested"


class CreditApplication(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="applications")
    status = models.CharField(max_length=24, choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED)
    credit_score = models.PositiveSmallIntegerField(null=True, blank=True)
    card_type = models.CharField(max_length=16, blank=True)
    credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    decision_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application {self.pk} ({self.status})"
