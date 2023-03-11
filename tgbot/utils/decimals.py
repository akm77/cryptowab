import decimal
from typing import Union


def format_decimal(value: Union[int, float, decimal.Decimal], delimiter="\'", pre=8):
    s = f"{value:,.{pre}f}"
    return s.replace(",", delimiter).rstrip('0').rstrip('.') if '.' in s else s


def value_to_decimal(value, decimal_places: int = 8) -> decimal.Decimal:
    decimal.getcontext().rounding = decimal.ROUND_HALF_UP  # define rounding method
    return decimal.Decimal(str(float(value))).quantize(decimal.Decimal('1e-{}'.format(decimal_places)))
