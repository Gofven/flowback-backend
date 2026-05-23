# Can use CrossHair for formal verification
# crosshair check flowback/poll/calculate_bet.py

# Small decimal (AT LEAST a magnitude below 10^(-6))
def get_small_decimal(power_of: int):
    """
    post: __return__ <= 1e-07
    """
    if power_of >= -6:
        return 10 ** -7
    return 10**power_of


def previous_outcome_avg_calculate(previous_outcomes: list[float]):
    """
    pre: all(0.0 <= x <= 1.0 for x in previous_outcomes)
    post: 0.0 <= __return__ <= 1.0
    """
    previous_outcome_avg = 0 if len(previous_outcomes) == 0 else sum(previous_outcomes) / len(previous_outcomes)
    return previous_outcome_avg
