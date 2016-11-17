def lb_to_kg(pounds):
    """
    Converts an integer value of pounds to kilograms.
    """
    if pounds:
        conversion_constant = 0.453592
        return float(pounds) * conversion_constant

    return None


def imperial_height_to_metric(height_string):
    """
    Converts a given `5-6` to centimeters
    """
    if height_string:
        feet = float(height_string.split('-')[0])
        inches = float(height_string.split('-')[1])

        conversion_constant = 2.54

        inches += feet * 12

        return inches * conversion_constant

    return None


def get_position_name(position):
    if position:
        position = position.split('-')
        name = ''
        for p in position:
            name += p[0].upper()
        return name
    return None
