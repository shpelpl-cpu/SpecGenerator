from __future__ import annotations

from collections import OrderedDict

from models import GroupedItem, InvoiceData


class InvoiceGrouper:

    def group(self, invoice: InvoiceData) -> list[GroupedItem]:

        groups: OrderedDict[str, GroupedItem] = OrderedDict()

        for item in invoice.items:

            if item.cn not in groups:

                groups[item.cn] = GroupedItem(
                    cn=item.cn,
                    description=item.description_pl,
                )

            group = groups[item.cn]

            group.quantity += item.quantity
            group.net_weight += item.net_weight
            group.gross_weight += item.gross_weight
            group.value += item.value

            if not group.description and item.description_pl:
                group.description = item.description_pl

        return list(groups.values())