"""Flow 1 – apply for a credit card. Orchestrates rating (flow 2) and decision (flow 3)."""
from django.db import IntegrityError, transaction
from rest_framework import status

from core import audit, events
from core.exceptions import BusinessError

from .models import ApplicationStatus, CreditApplication, Customer

IDENTITY_FIELDS = ("first_name", "last_name", "date_of_birth")
PROFILE_FIELDS = (
    "email", "phone", "employment_type", "employer_name", "job_title",
    "annual_salary", "existing_credit_cards",
)


def _find_or_create_customer(data: dict) -> Customer:
    lookup = {"id_document_type": data["id_document_type"], "id_document_number": data["id_document_number"]}
    customer = Customer.objects.select_for_update().filter(**lookup).first()

    if customer is None:
        try:
            with transaction.atomic():
                return Customer.objects.create(**data)
        except IntegrityError:  # lost a race with a parallel request
            customer = Customer.objects.select_for_update().get(**lookup)

    mismatched = [
        f for f in IDENTITY_FIELDS
        if str(getattr(customer, f)).strip().lower() != str(data[f]).strip().lower()
    ]
    if mismatched:
        raise BusinessError(
            "identity_mismatch",
            "This identity document is already registered with different personal details.",
            status.HTTP_409_CONFLICT,
            {f: ["Does not match our records for this document."] for f in mismatched},
        )

    for f in PROFILE_FIELDS:  # refresh employment / contact info with the latest submission
        setattr(customer, f, data[f])
    customer.save()
    return customer


def _ensure_can_apply(customer: Customer):
    open_app = customer.applications.filter(
        status__in=[ApplicationStatus.APPROVED, ApplicationStatus.DOCUMENTS_REQUESTED]
    ).first()
    if open_app is None:
        return
    if open_app.status == ApplicationStatus.APPROVED:
        raise BusinessError(
            "already_has_card", "You already hold a card from us. One application per customer.",
            status.HTTP_409_CONFLICT,
        )
    raise BusinessError(
        "documents_pending",
        "Your earlier application is waiting for additional documents.",
        status.HTTP_409_CONFLICT,
    )


@transaction.atomic
def submit_application(data: dict):
    """Returns (application, card_or_None, plain_first_time_pin_or_None)."""
    from cards import services as card_services
    from credit_rating import services as rating_services

    customer = _find_or_create_customer(dict(data))
    _ensure_can_apply(customer)

    application = CreditApplication.objects.create(customer=customer)
    audit.record("APPLICATION_SUBMITTED", "application", application.pk, customer_id=customer.pk)
    events.publish("application.submitted", application_id=application.pk, customer_id=customer.pk)

    # Flow 2 – credit rating
    score, source = rating_services.get_or_calculate_score(customer)
    application.credit_score = score
    application.save(update_fields=["credit_score"])
    audit.record("CREDIT_SCORE_SET", "customer", customer.pk, score=score, source=source)
    events.publish("credit.score.determined", application_id=application.pk, score=score)

    # Flow 3 – decision and card issuance
    card, pin = card_services.decide_and_issue(application)
    return application, card, pin
