def estimate_label_fee(weight_oz: float) -> float:
    """Estimate USPS shipping label cost based on package weight."""
    if weight_oz <= 3:
        return 4.99   # USPS First Class (up to 3 oz)
    if weight_oz <= 16:
        return 6.99   # USPS First Class (up to 1 lb)
    if weight_oz <= 48:
        return 9.99   # USPS Priority Mail (up to 3 lbs)
    return 14.99      # USPS Priority Mail flat rate
