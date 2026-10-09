from django.test import SimpleTestCase

from applications.models import ApplicationStatus
from cards.services import decide


class DecisionTableTests(SimpleTestCase):
    def test_500_platinum_40k(self):
        s, t, limit, _ = decide(500)
        self.assertEqual((s, t, limit), (ApplicationStatus.APPROVED, "PLATINUM", 40_000))

    def test_300_gold_20k(self):
        s, t, limit, _ = decide(300)
        self.assertEqual((s, t, limit), (ApplicationStatus.APPROVED, "GOLD", 20_000))

    def test_150_visa_10k(self):
        s, t, limit, _ = decide(150)
        self.assertEqual((s, t, limit), (ApplicationStatus.APPROVED, "VISA", 10_000))

    def test_50_requests_documents(self):
        s, t, limit, _ = decide(50)
        self.assertEqual(s, ApplicationStatus.DOCUMENTS_REQUESTED)
        self.assertIsNone(t)
        self.assertIsNone(limit)

    def test_below_minimum_rejected(self):
        self.assertEqual(decide(10)[0], ApplicationStatus.REJECTED)
