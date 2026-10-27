from decimal import ROUND_HALF_UP, Decimal


def to_minor(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def to_major(minor: int) -> float:
    return minor / 100
