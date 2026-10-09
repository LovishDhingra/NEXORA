from datetime import date

from django.test import SimpleTestCase

from core import validators


class ValidatorTests(SimpleTestCase):
    def test_luhn_roundtrip(self):
        partial = "453201511283036"
        number = partial + validators.luhn_check_digit(partial)
        self.assertTrue(validators.passes_luhn(number))
        self.assertFalse(validators.passes_luhn(number[:-1] + str((int(number[-1]) + 1) % 10)))

    def test_known_luhn_number(self):
        self.assertTrue(validators.passes_luhn("4539578763621486"))

    def test_age(self):
        self.assertEqual(validators.age_in_years(date(2000, 6, 15), date(2024, 6, 14)), 23)
        self.assertEqual(validators.age_in_years(date(2000, 6, 15), date(2024, 6, 15)), 24)

    def test_document_numbers(self):
        self.assertIsNone(validators.check_document_number("PASSPORT", "k 1234567"))
        self.assertIsNotNone(validators.check_document_number("SSN", "12-34"))
        self.assertIsNone(validators.check_document_number("SSN", "123-45-6789"))

    def test_pin_rules(self):
        self.assertIsNone(validators.pin_problem("7391"))
        for bad in ("123", "12345", "abcd", "1111", "1234"):
            self.assertIsNotNone(validators.pin_problem(bad), bad)
