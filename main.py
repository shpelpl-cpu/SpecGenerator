from pathlib import Path

from exporter import Exporter
from grouper import InvoiceGrouper
from mapper import DescriptionMapper
from parser import InvoiceParser
from validator import InvoiceValidator


def main():

    print("Wczytywanie faktury...")

    parser = InvoiceParser("invoice.xlsx")
    invoice = parser.parse()

    print(f"Pozycji: {len(invoice.items)}")

    mapper = DescriptionMapper()

    unknown = []

    for item in invoice.items:

        try:
            item.description_pl = mapper.map(
                item.description_original
            )

        except ValueError:
            unknown.append(item.description_original)

    if unknown:

        print()
        print("========================================")
        print("NOWE OPISY")
        print("========================================")

        for value in sorted(set(unknown)):
            print(value)

        return

    print("Grupowanie...")

    groups = InvoiceGrouper().group(invoice)

    print(f"Kodów CN: {len(groups)}")

    validator = InvoiceValidator()

    result = validator.validate(
        invoice,
        groups
    )

    if not result.success:

        print()
        print("========================================")
        print("BŁĘDY")
        print("========================================")

        for error in result.errors:
            print(error)

        return

    print("Eksport...")

    output = Path("output") / "specyfikacja_wypelniona.xlsx"

    Exporter(
        "templates/spec_template.xlsx"
    ).export(
        groups,
        output
    )

    print()
    print("========================================")
    print("GOTOWE")
    print("========================================")
    print(output.resolve())


if __name__ == "__main__":
    main()