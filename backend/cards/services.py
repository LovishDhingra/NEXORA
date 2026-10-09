"""Flow 3 (decision + card issuance) and Flow 4 (first-time PIN change)."""
import secrets
from datetime import date

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework import status

from applications.models import ApplicationStatus
from core import audit, events, validators
from core.exceptions import BusinessError

from .models import CardType, CreditCard

# (minimum score, card type, credit limit in USD) – highest tier first
TIERS = [
    (500, CardType.PLATINUM, 40_000),
    (300, CardType.GOLD, 20_000),
    (150, CardType.VISA, 10_000),
]
MIN_SCORE_FOR_DOCUMENT_REQUEST = 50


def decide(score: int):
    """Pure decision function: returns (status, card_type or None, limit or None, reason)."""
    for minimum, card_type, limit in TIERS:
        if score >= minimum:
            return ApplicationStatus.APPROVED, card_type, limit, f"Credit score {score} qualifies for a {card_type.label} card."
    if score >= MIN_SCORE_FOR_DOCUMENT_REQUEST:
        return ApplicationStatus.DOCUMENTS_REQUESTED, None, None, f"Credit score {score}: additional documents are required."
    return ApplicationStatus.REJECTED, None, None, f"Credit score {score} is below our minimum."


def generate_card_number() -> str:
    while True:
        partial = "4" + "".join(secrets.choice("0123456789") for _ in range(14))
        number = partial + validators.luhn_check_digit(partial)
        if not CreditCard.objects.filter(card_number=number).exists():
            return number


def generate_first_time_pin() -> str:
    while True:
        pin = "".join(secrets.choice("0123456789") for _ in range(4))
        if validators.pin_problem(pin) is None:
            return pin


def _expiry() -> date:
    today = timezone.now().date()
    return date(today.year + settings.CARD_VALIDITY_YEARS, today.month, 1)


def decide_and_issue(application):
    """Apply the decision table. Returns (card_or_None, plain_pin_or_None)."""
    new_status, card_type, limit, reason = decide(application.credit_score)
    application.status = new_status
    application.decision_reason = reason
    application.decided_at = timezone.now()

    card = pin = None
    if new_status == ApplicationStatus.APPROVED:
        pin = generate_first_time_pin()
        card = CreditCard.objects.create(
            application=application,
            customer=application.customer,
            card_number=generate_card_number(),
            card_type=card_type,
            credit_limit=limit,
            expires_on=_expiry(),
            pin_hash=make_password(pin),
        )
        application.card_type = card_type
        application.credit_limit = limit
        audit.record("CARD_ISSUED", "card", card.pk, application_id=application.pk, card_type=card_type, last4=card.card_number[-4:])
    application.save()

    audit.record("APPLICATION_DECIDED", "application", application.pk, status=new_status, score=application.credit_score)
    events.publish("application.decided", application_id=application.pk, status=new_status)
    if card:
        events.publish("card.issued", card_id=card.pk, application_id=application.pk)
    return card, pin


def change_first_time_pin(*, card_number, first_time_pin, id_document_number, new_pin):
    """Flow 4. The failure path commits its counter update before raising."""
    from django.db import transaction

    failure = None
    with transaction.atomic():
        card = (
            CreditCard.objects.select_for_update().select_related("customer").filter(card_number=card_number).first()
        )
        if card is None:
            failure = BusinessError("verification_failed", "We could not verify those card details.")
        elif card.is_locked:
            failure = BusinessError(
                "card_locked", "This card is locked after too many failed attempts. Please contact the bank.",
                status.HTTP_423_LOCKED,
            )
        elif not card.pin_is_default:
            failure = BusinessError(
                "pin_already_changed", "The first-time PIN was already changed for this card.", status.HTTP_409_CONFLICT
            )
        else:
            pin_ok = check_password(first_time_pin, card.pin_hash)
            doc_ok = validators.normalize_document_number(card.customer.id_document_number) == id_document_number
            if not (pin_ok and doc_ok):
                card.failed_pin_attempts += 1
                if card.failed_pin_attempts >= settings.MAX_PIN_ATTEMPTS:
                    card.is_locked = True
                card.save(update_fields=["failed_pin_attempts", "is_locked"])
                audit.record("PIN_CHANGE_FAILED", "card", card.pk, attempts=card.failed_pin_attempts, locked=card.is_locked)
                failure = BusinessError("verification_failed", "We could not verify those card details.")
            else:
                card.pin_hash = make_password(new_pin)
                card.pin_is_default = False
                card.failed_pin_attempts = 0
                card.pin_changed_at = timezone.now()
                card.save(update_fields=["pin_hash", "pin_is_default", "failed_pin_attempts", "pin_changed_at"])
                audit.record("PIN_CHANGED", "card", card.pk, last4=card.card_number[-4:])
                events.publish("card.pin_changed", card_id=card.pk)

    if failure:
        raise failure
    return card
