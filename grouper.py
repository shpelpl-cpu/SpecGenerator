from __future__ import annotations

from collections import OrderedDict

from mapper import build_description, gender_bucket, product_key
from models import GroupedItem, InvoiceData


class InvoiceGrouper:

    def group(self, invoice: InvoiceData) -> list[GroupedItem]:

        groups: OrderedDict[tuple[str, str, str], GroupedItem] = OrderedDict()

        for item in invoice.items:

            item_key = product_key(item.cn, item.description_original)
            key = (item.cn, item_key, item.gender)

            if key not in groups:

                groups[key] = GroupedItem(
                    cn=item.cn,
                    description=item.description_pl,
                    gender=item.gender,
                    description_parts=[item_key],
                    genders={item.gender} if item.gender else set(),
                )

            group = groups[key]

            group.quantity += item.quantity
            group.net_weight += item.net_weight
            group.gross_weight += item.gross_weight
            group.value += item.value

        merged_groups: OrderedDict[tuple[str, str, str], GroupedItem] = OrderedDict()

        for group in groups.values():
            key = (
                group.cn,
                group.description_parts[0],
                gender_bucket(group.gender),
            )

            if key not in merged_groups:
                merged_groups[key] = GroupedItem(
                    cn=group.cn,
                    description=group.description,
                    gender=group.gender,
                    description_parts=group.description_parts.copy(),
                    genders=group.genders.copy(),
                    quantity=group.quantity,
                    net_weight=group.net_weight,
                    gross_weight=group.gross_weight,
                    value=group.value,
                )
            else:
                merged_group = merged_groups[key]
                merged_group.quantity += group.quantity
                merged_group.net_weight += group.net_weight
                merged_group.gross_weight += group.gross_weight
                merged_group.value += group.value
                merged_group.genders.update(group.genders)

        for group in merged_groups.values():
            group.description = build_description(
                group.cn,
                group.description_parts[0],
                group.genders,
            )

        special_key = ("6109902000", "tshirts")
        special_groups = [
            group
            for group in merged_groups.values()
            if (group.cn, group.description_parts[0]) == special_key
        ]

        if len(special_groups) > 1:
            special_groups.sort(
                key=lambda group: gender_bucket(group.gender),
            )
            combined = GroupedItem(
                cn=special_key[0],
                description=", ".join(
                    f"{group.description} ({format(group.quantity.normalize(), 'f')} szt)"
                    for group in special_groups
                ),
                description_parts=[special_key[1]],
                genders=set().union(*(group.genders for group in special_groups)),
                has_quantity_breakdown=True,
                quantity=sum(group.quantity for group in special_groups),
                net_weight=sum(group.net_weight for group in special_groups),
                gross_weight=sum(group.gross_weight for group in special_groups),
                value=sum(group.value for group in special_groups),
            )

            for key in list(merged_groups):
                if key[0] == special_key[0] and key[1] == special_key[1]:
                    del merged_groups[key]

            merged_groups[(special_key[0], special_key[1], "combined")] = combined

        product_order = {
            "6114300000": {
                "tshirts": 0,
                "bodysuit": 1,
                "jumpsuit": 2,
            },
            "6211439000": {
                "bodysuit": 0,
                "jumpsuit": 1,
                "vest": 2,
                "halter top": 3,
            },
        }

        return sorted(
            merged_groups.values(),
            key=lambda group: (
                group.cn,
                product_order.get(group.cn, {}).get(
                    group.description_parts[0],
                    0,
                ),
                group.description,
            ),
        )
