import json

from webutils.converter.abc_converter import Converter
from webutils.converter.ast import Node


class JsonConverter(Converter):
    """Converter for JSON format using the built-in json module."""

    def _load(self, fp) -> Node:
        """
        Load JSON from the given text stream and convert it to AST.

        :param fp: A text stream to read JSON from.
        :return: Root of the constructed AST.
        """
        data = json.load(fp)
        return Node.from_native(data)

    def _dump(self, node: Node, fp) -> None:
        """
        Serialize the AST node to JSON and write it to the text stream.

        :param node: The root AST node to serialize.
        :param fp: A text stream to write JSON to.
        """
        json.dump(
            node.to_native(),
            fp,
            ensure_ascii=False,
            indent=2,
        )
