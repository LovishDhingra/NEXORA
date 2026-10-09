from django.test import SimpleTestCase

from credit_rating.services import calculate_score


class CalculateScoreTests(SimpleTestCase):
    def test_two_or_more_cards_scores_300_regardless_of_salary(self):
        self.assertEqual(calculate_score(500_000, 2), 300)
        self.assertEqual(calculate_score(10_000, 5), 300)

    def test_salary_above_200k_scores_500(self):
        self.assertEqual(calculate_score(200_001, 0), 500)

    def test_salary_between_50k_and_200k_scores_150_inclusive(self):
        self.assertEqual(calculate_score(200_000, 1), 150)
        self.assertEqual(calculate_score(50_000, 0), 150)
        self.assertEqual(calculate_score(120_000, 1), 150)

    def test_salary_below_50k_scores_50(self):
        self.assertEqual(calculate_score("49999.99", 0), 50)
