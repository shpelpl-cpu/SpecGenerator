from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List


@dataclass(slots=True)
class InvoiceItem:
    """
    Pojedyncza pozycja odczytana z faktury.
    """

    row_number: int

    cn: str
    description_original: str
    gender: str = ""
    description_pl: str = ""

    quantity: Decimal = Decimal("0")
    net_weight: Decimal = Decimal("0")
    gross_weight: Decimal = Decimal("0")
    value: Decimal = Decimal("0")

@dataclass(slots=True)
class GroupedItem:
    """
    Zgrupowane dane według kodu CN.
    """

    cn: str
    description: str
    gender: str = ""
    description_parts: list[str] = field(default_factory=list)
    genders: set[str] = field(default_factory=set)
    has_quantity_breakdown: bool = False

    quantity: Decimal = Decimal("0")
    net_weight: Decimal = Decimal("0")
    gross_weight: Decimal = Decimal("0")
    value: Decimal = Decimal("0")


@dataclass(slots=True)
class ValidationResult:
    """
    Wynik kontroli poprawności.
    """

    success: bool
    errors: List[str] = field(default_factory=list)


@dataclass(slots=True)
class InvoiceData:
    """
    Wszystkie pozycje odczytane z faktury.
    """

    items: List[InvoiceItem] = field(default_factory=list)

    @property
    def total_quantity(self) -> Decimal:
        return sum((i.quantity for i in self.items), Decimal("0"))

    @property
    def total_net_weight(self) -> Decimal:
        return sum((i.net_weight for i in self.items), Decimal("0"))

    @property
    def total_gross_weight(self) -> Decimal:
        return sum((i.gross_weight for i in self.items), Decimal("0"))

    @property
    def total_value(self) -> Decimal:
        return sum((i.value for i in self.items), Decimal("0"))

    @property
    def unique_cn(self) -> list[str]:
        return sorted({i.cn for i in self.items})
