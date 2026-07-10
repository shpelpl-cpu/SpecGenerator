from __future__ import annotations

from copy import copy
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from models import GroupedItem


class Exporter:

    DATA_START_ROW = 2

    COL_LP = 1
    COL_CN = 2
    COL_QTY = 3
    COL_NET = 4
    COL_GROSS = 5
    COL_VALUE = 6
    COL_CURRENCY = 7
    COL_UNIT = 8
    COL_DESCRIPTION = 9
    COL_ORIGIN = 10
    COL_PREF = 11

    def __init__(self, template_path: str | Path):

        self.template_path = Path(template_path)

        if not self.template_path.exists():
            raise FileNotFoundError(self.template_path)

    @staticmethod
    def _number(value: Decimal) -> float:

        if value is None:
            return 0.0

        return float(value)

    @staticmethod
    def _copy_style(source, target):

        target._style = copy(source._style)

    @staticmethod
    def _move_row_dimensions(
        sheet: Worksheet,
        start_row: int,
        amount: int,
    ):

        """Move row metadata which openpyxl does not move with cells."""

        rows_to_move = [
            row
            for row in sheet.row_dimensions
            if row >= start_row
        ]

        for row in sorted(rows_to_move, reverse=True):

            dimension = copy(sheet.row_dimensions[row])
            dimension.index = row + amount

            sheet.row_dimensions[row + amount] = dimension
            del sheet.row_dimensions[row]

    @staticmethod
    def _move_merged_cells(
        sheet: Worksheet,
        start_row: int,
        amount: int,
    ):

        """Keep merged ranges aligned with the rows moved by insert_rows."""

        merged_ranges = list(sheet.merged_cells.ranges)

        sheet.merged_cells.ranges.clear()

        for merged_range in merged_ranges:

            if merged_range.min_row >= start_row:
                merged_range.shift(row_shift=amount)

            elif merged_range.max_row >= start_row:
                merged_range.max_row += amount

            sheet.merged_cells.add(merged_range)
            merged_range.format()

    def _insert_rows(
        self,
        sheet: Worksheet,
        amount: int,
    ):

        if amount <= 0:
            return

        insert_at = self.DATA_START_ROW + 1
        template_row = self.DATA_START_ROW
        max_column = sheet.max_column

        self._move_row_dimensions(
            sheet,
            insert_at,
            amount,
        )

        sheet.insert_rows(
            insert_at,
            amount
        )

        self._move_merged_cells(
            sheet,
            insert_at,
            amount,
        )

        for row in range(
            insert_at,
            insert_at + amount,
        ):

            template_dimension = copy(
                sheet.row_dimensions[template_row]
            )
            template_dimension.index = row
            sheet.row_dimensions[row] = template_dimension

            for col in range(
                1,
                max_column + 1
            ):

                src = sheet.cell(template_row, col)
                dst = sheet.cell(row, col)

                self._copy_style(src, dst)

    def _write_row(
        self,
        sheet: Worksheet,
        row: int,
        lp: int,
        group: GroupedItem,
    ):

        sheet.cell(row, self.COL_LP).value = lp

        sheet.cell(row, self.COL_CN).value = group.cn

        sheet.cell(row, self.COL_QTY).value = self._number(
            group.quantity
        )

        sheet.cell(row, self.COL_NET).value = self._number(
            group.net_weight
        )

        sheet.cell(row, self.COL_GROSS).value = self._number(
            group.gross_weight
        )

        sheet.cell(row, self.COL_VALUE).value = self._number(
            group.value
        )

        sheet.cell(row, self.COL_CURRENCY).value = "EUR"

        sheet.cell(row, self.COL_UNIT).value = "PCS"

        sheet.cell(
            row,
            self.COL_DESCRIPTION
        ).value = group.description

        sheet.cell(
            row,
            self.COL_ORIGIN
        ).value = "CN"

        sheet.cell(
            row,
            self.COL_PREF
        ).value = "100"


    def export(
        self,
        groups: list[GroupedItem],
        output_path: str | Path,
    ):

        workbook = load_workbook(
            self.template_path
        )

        sheet = workbook.active

        if len(groups) > 1:

            self._insert_rows(
                sheet,
                len(groups) - 1
            )

        row = self.DATA_START_ROW

        lp = 1

        for group in groups:

            self._write_row(
                sheet,
                row,
                lp,
                group
            )

            row += 1
            lp += 1

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        workbook.save(output_path)

        workbook.close()
