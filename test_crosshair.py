# Run: crosshair check test_crosshair.py
# Or:  crosshair check flowback/poll/calculate_bet.py

from flowback.poll.calculate_bet import (
    get_small_decimal,
    previous_outcome_avg_calculate,
    no_previous_history_calculate,
)


def test_small_decimal_always_small(power_of: int):
    """
    post: __return__ <= 1e-07
    """
    return get_small_decimal(power_of)


def test_previous_outcome_avg_bounded(previous_outcomes: list[float]):
    """
    pre: all(x == 0 or x == 1 for x in previous_outcomes)
    post: 0.0 <= __return__ <= 1.0
    """
    return previous_outcome_avg_calculate(previous_outcomes)


def test_no_history_returns_none_when_all_none(n: int):
    """
    pre: 1 <= n <= 5
    post: __return__ is None
    """
    current_bets = [[None] for _ in range(n)]
    return no_previous_history_calculate(current_bets, 0)


def test_no_history_average_bounded(current_bets: list[list[float | None]], i: int):
    """
    pre: len(current_bets) > 0
    pre: all(len(bets) > i for bets in current_bets)
    pre: 0 <= i
    pre: all(bets[i] is None or (0.0 <= bets[i] <= 1.0) for bets in current_bets)
    post: __return__ is None or 0.0 <= __return__ <= 1.0
    """
    return no_previous_history_calculate(current_bets, i)
