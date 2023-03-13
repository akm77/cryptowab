from typing import Callable, TypeVar

import decimal
from typing import Union

T = TypeVar("T")
TypeFactory = Callable[[str], T]


def format_decimal(value: Union[int, float, decimal.Decimal], delimiter="\'", pre=8):
    s = f"{value:,.{pre}f}"
    return s.replace(",", delimiter).rstrip('0').rstrip('.') if '.' in s else s


def value_to_decimal(value, decimal_places: int = 8) -> decimal.Decimal:
    decimal.getcontext().rounding = decimal.ROUND_HALF_UP  # define rounding method
    return decimal.Decimal(str(float(value))).quantize(decimal.Decimal('1e-{}'.format(decimal_places)))


def check_digit_value(text: str, type_factory: TypeFactory[T] = int, min=1, max=999):
    # type_factory: TypeFactory[T] = type_factory
    try:
        value = d if min <= (d := type_factory(text)) <= max else 1
    except ValueError:
        value = 1
    return value
