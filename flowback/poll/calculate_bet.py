# Can use crosshair for formal verification
# crosshair check flowback/poll/calculate_bet.py

# Small decimal (AT LEAST a magnitude below 10^(-6))
def get_small_decimal(power_of: int):
    """
    post: __return__ <= 1e-07
    """
    if power_of >= -6:
        return 10 ** -7
    return 10**power_of
