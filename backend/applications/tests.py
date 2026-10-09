from django.test import TestCase
from rest_framework.test import APIClient

from applications.models import Customer, ExistingCard
from cards.models import CreditCard
from core.models import AuditLog

APPLY_URL = "/api/applications/"
PIN_URL = "/api/cards/change-pin/"
TWO_CARDS = [{"issuer": "HDFC", "network": "VISA"}, {"issuer": "SBI", "network": "RUPAY"}]


def payload(**overrides):
    base = {
        "first_name": "Asha", "last_name": "Verma", "date_of_birth": "1990-04-12",
        "email": "asha@example.com", "phone": "+14155550123",
        "employment_type": "SALARIED", "employer_name": "Northwind", "job_title": "Engineer",
        "annual_salary": "120000", "existing_credit_cards": 0,
        "id_document_type": "PASSPORT", "id_document_number": "k1234567",
    }
    base.update(overrides)
    return base


class ApplyFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def apply(self, **overrides):
        return self.client.post(APPLY_URL, payload(**overrides), format="json")

    def test_mid_salary_gets_visa_card_with_pin(self):
        r = self.apply()
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "APPROVED")
        self.assertEqual(r.data["credit_score"], 150)
        self.assertEqual(r.data["card"]["card_type"], "VISA")
        self.assertEqual(len(r.data["card"]["card_number"]), 16)
        self.assertRegex(r.data["card"]["first_time_pin"], r"^\d{4}$")
        self.assertTrue(AuditLog.objects.filter(action="CARD_ISSUED").exists())

    def test_high_salary_platinum(self):
        r = self.apply(annual_salary="250000", id_document_number="P7654321")
        self.assertEqual((r.data["card"]["card_type"], r.data["credit_limit"]), ("PLATINUM", "40000.00"))

    def test_two_cards_gold(self):
        r = self.apply(existing_credit_cards=2, other_cards=TWO_CARDS, annual_salary="30000", id_document_number="G7654321")
        self.assertEqual((r.data["credit_score"], r.data["card"]["card_type"]), (300, "GOLD"))

    def test_other_cards_are_saved_with_the_customer(self):
        self.apply(existing_credit_cards=2, other_cards=TWO_CARDS, id_document_number="G7654321")
        saved = ExistingCard.objects.filter(customer__id_document_number="G7654321")
        self.assertEqual(sorted(saved.values_list("issuer", "network")), [("HDFC", "VISA"), ("SBI", "RUPAY")])

    def test_number_of_cards_must_match_the_details(self):
        r = self.apply(existing_credit_cards=2, other_cards=TWO_CARDS[:1])
        self.assertEqual(r.status_code, 400)
        self.assertIn("other_cards", r.data["error"]["fields"])
        self.assertEqual(ExistingCard.objects.count(), 0)

    def test_low_salary_requests_documents_and_issues_no_card(self):
        r = self.apply(annual_salary="30000", id_document_number="L7654321")
        self.assertEqual(r.data["status"], "DOCUMENTS_REQUESTED")
        self.assertIsNone(r.data["card"])
        self.assertEqual(CreditCard.objects.count(), 0)

    def test_existing_score_is_reused(self):
        r = self.apply(annual_salary="30000", id_document_number="L7654321")
        customer = Customer.objects.get(id_document_number="L7654321")
        self.assertEqual(customer.credit_score, 50)
        # a second attempt is blocked while documents are pending
        r2 = self.apply(annual_salary="900000", id_document_number="L7654321")
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(r2.data["error"]["code"], "documents_pending")

    def test_second_application_after_approval_blocked(self):
        self.apply()
        r = self.apply()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"]["code"], "already_has_card")

    def test_same_document_different_person_is_rejected(self):
        self.apply()
        r = self.apply(first_name="Someone", last_name="Else")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"]["code"], "identity_mismatch")

    def test_validation_errors_use_the_standard_envelope(self):
        r = self.apply(date_of_birth="2015-01-01", email="nope", phone="12", annual_salary="-5", id_document_number="!!")
        self.assertEqual(r.status_code, 400)
        err = r.data["error"]
        self.assertEqual(err["code"], "validation_error")
        for field in ("date_of_birth", "email", "phone", "annual_salary"):
            self.assertIn(field, err["fields"])

    def test_missing_fields_are_reported(self):
        r = self.client.post(APPLY_URL, {}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("first_name", r.data["error"]["fields"])

    def test_get_application_masks_card(self):
        created = self.apply()
        r = self.client.get(f"{APPLY_URL}{created.data['id']}/")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("card_number", r.data["card"])
        self.assertNotIn("first_time_pin", r.data["card"])

    def test_unknown_application_404_envelope(self):
        r = self.client.get(f"{APPLY_URL}9999/")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.data["error"]["code"], "not_found")


class ChangePinTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        r = self.client.post(APPLY_URL, payload(), format="json")
        self.card = r.data["card"]

    def body(self, **o):
        b = {
            "card_number": self.card["card_number"], "first_time_pin": self.card["first_time_pin"],
            "id_document_number": "K1234567", "new_pin": "7391", "confirm_pin": "7391",
        }
        b.update(o)
        return b

    def test_success_updates_pin_and_audits(self):
        r = self.client.post(PIN_URL, self.body(), format="json")
        self.assertEqual(r.status_code, 200, r.data)
        card = CreditCard.objects.get()
        self.assertFalse(card.pin_is_default)
        self.assertTrue(AuditLog.objects.filter(action="PIN_CHANGED").exists())

    def test_cannot_change_twice(self):
        self.client.post(PIN_URL, self.body(), format="json")
        r = self.client.post(PIN_URL, self.body(first_time_pin="7391", new_pin="8264", confirm_pin="8264"), format="json")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.data["error"]["code"], "pin_already_changed")

    def test_wrong_document_fails_and_counts(self):
        r = self.client.post(PIN_URL, self.body(id_document_number="X9999999"), format="json")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(CreditCard.objects.get().failed_pin_attempts, 1)

    def test_card_locks_after_five_failures(self):
        for _ in range(5):
            self.client.post(PIN_URL, self.body(first_time_pin="0001"), format="json")
        r = self.client.post(PIN_URL, self.body(), format="json")
        self.assertEqual(r.status_code, 423)
        self.assertEqual(r.data["error"]["code"], "card_locked")

    def test_unknown_card_is_generic_failure(self):
        r = self.client.post(PIN_URL, self.body(card_number="4539578763621486"), format="json")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(r.data["error"]["code"], "verification_failed")

    def test_input_validation(self):
        r = self.client.post(PIN_URL, self.body(confirm_pin="7392"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("confirm_pin", r.data["error"]["fields"])
        r = self.client.post(PIN_URL, self.body(new_pin="1111", confirm_pin="1111"), format="json")
        self.assertIn("new_pin", r.data["error"]["fields"])
        r = self.client.post(PIN_URL, self.body(card_number="1234567890123456"), format="json")
        self.assertIn("card_number", r.data["error"]["fields"])
