"""Pure validation helpers (no Django imports) so they are trivial to unit test."""
import re
from datetime import date

DOCUMENT_PATTERNS = {
    "PASSPORT": (r"^[A-Z0-9]{6,9}$", "Passport numbers have 6–9 letters or digits."),
    "NATIONAL_ID": (r"^[A-Z0-9]{8,16}$", "National ID numbers have 8–16 letters or digits."),
    "DRIVING_LICENSE": (r"^[A-Z0-9]{8,20}$", "Driving licence numbers have 8–20 letters or digits."),
    "SSN": (r"^\d{9}$", "A social security number has 9 digits."),
}

PHONE_RE = re.compile(r"^\+?\d{10,15}$")
WEAK_PINS = {"0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999", "1234", "4321", "2580", "0852"}


def normalize_document_number(value: str) -> str:
    return re.sub(r"[\s-]", "", value or "").upper()


def check_document_number(doc_type: str, number: str):
    """Return an error message, or None when the number looks right for its type."""
    pattern = DOCUMENT_PATTERNS.get(doc_type)
    if not pattern:
        return "Unknown document type."
    regex, message = pattern
    return None if re.match(regex, normalize_document_number(number)) else message


def normalize_phone(value: str) -> str:
    return re.sub(r"[\s()-]", "", value or "")


def is_valid_phone(value: str) -> bool:
    return bool(PHONE_RE.match(normalize_phone(value)))


def age_in_years(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def luhn_check_digit(partial: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(partial)):
        d = int(ch)
        if i % 2 == 0:  # these positions get doubled once the check digit is appended
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def passes_luhn(number: str) -> bool:
    return number.isdigit() and len(number) > 1 and luhn_check_digit(number[:-1]) == number[-1]


def pin_problem(pin: str):
    """Return why a PIN is unacceptable, or None."""
    if not re.fullmatch(r"\d{4}", pin or ""):
        return "A PIN must be exactly 4 digits."
    if pin in WEAK_PINS:
        return "That PIN is too easy to guess. Avoid repeated or sequential digits."
    return None
