import csv

from webutils.converter.abc_converter import Converter
from webutils.converter.ast import Node


class CsvConverter(Converter):
    """Converter for CSV format using the built-in csv module."""

    def _load(self, fp) -> Node:
        """
        Load CSV from the given text stream and convert it to AST.

        :param fp: A text stream to read CSV from.
        :return: Root of the constructed AST.
        """
        reader = csv.DictReader(fp)
        rows = list(reader)
        # Represent CSV as a list of objects
        return Node.from_native(rows)

    def _dump(self, node: Node, fp) -> None:
        """
        Serialize the AST node to CSV and write it to the text stream.

        :param node: The root AST node to serialize.
        :param fp: A text stream to write CSV to.
        :raises ValueError: If the native object is not a non-empty list
                            of dictionaries.
        """
        native = node.to_native()
        if not isinstance(native, list) or not native:
            raise ValueError("For CSV, a non-empty list of dicts is expected")

        fieldnames = list(native[0].keys())
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(native)
