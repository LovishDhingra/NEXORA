"""Flow 2 – customer credit rating.

Rules are evaluated top to bottom, as listed in the problem statement:
    2+ credit cards held            -> 300
    salary  > 200,000               -> 500
    50,000 <= salary <= 200,000     -> 150
    salary  < 50,000                -> 50
"""
from decimal import Decimal

HIGH_SALARY = Decimal("200000")
MID_SALARY = Decimal("50000")

SCORE_MANY_CARDS = 300
SCORE_HIGH_SALARY = 500
SCORE_MID_SALARY = 150
SCORE_LOW_SALARY = 50


def calculate_score(annual_salary, card_count: int) -> int:
    salary = Decimal(annual_salary)
    if card_count >= 2:
        return SCORE_MANY_CARDS
    if salary > HIGH_SALARY:
        return SCORE_HIGH_SALARY
    if salary >= MID_SALARY:
        return SCORE_MID_SALARY
    return SCORE_LOW_SALARY


def get_or_calculate_score(customer):
    """Return (score, source). Reuses an existing score, otherwise calculates and stores one."""
    if customer.credit_score is not None:
        return customer.credit_score, "existing"

    cards_held = customer.existing_credit_cards + customer.cards.count()
    score = calculate_score(customer.annual_salary, cards_held)
    customer.credit_score = score
    customer.save(update_fields=["credit_score", "updated_at"])
    return score, "calculated"
