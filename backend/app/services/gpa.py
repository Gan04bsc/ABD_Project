def calc_gpa(grades: list[float]) -> float:
    if not grades:
        return 0.0
    return round(sum(grades) / len(grades), 2)
