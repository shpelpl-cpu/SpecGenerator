from __future__ import annotations

from decimal import Decimal

from models import GroupedItem, InvoiceData, ValidationResult


class InvoiceValidator:

    def validate(
        self,
        invoice: InvoiceData,
        groups: list[GroupedItem]
    ) -> ValidationResult:

        result = ValidationResult(success=True)

        # suma ilości

        qty = sum(
            (g.quantity for g in groups),
            Decimal("0")
        )

        if qty != invoice.total_quantity:

            result.success = False

            result.errors.append(

                f"Ilość niezgodna "
                f"({qty} != {invoice.total_quantity})"

            )

        # suma netto

        net = sum(
            (g.net_weight for g in groups),
            Decimal("0")
        )

        if net != invoice.total_net_weight:

            result.success = False

            result.errors.append(

                f"Waga netto niezgodna "
                f"({net} != {invoice.total_net_weight})"

            )

        # suma brutto

        gross = sum(
            (g.gross_weight for g in groups),
            Decimal("0")
        )

        if gross != invoice.total_gross_weight:

            result.success = False

            result.errors.append(

                f"Waga brutto niezgodna "
                f"({gross} != {invoice.total_gross_weight})"

            )

        # suma wartości

        value = sum(
            (g.value for g in groups),
            Decimal("0")
        )

        if value != invoice.total_value:

            result.success = False

            result.errors.append(

                f"Wartość niezgodna "
                f"({value} != {invoice.total_value})"

            )

        # brak opisu

        for group in groups:

            if not group.description:

                result.success = False

                result.errors.append(

                    f"Brak opisu dla CN {group.cn}"

                )

        return result