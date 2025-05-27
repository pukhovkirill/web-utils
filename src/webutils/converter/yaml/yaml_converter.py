import yaml

from webutils.converter.abc_converter import Converter
from webutils.converter.ast import Node


class YamlConverter(Converter):
    """Converter for YAML format using PyYAML safe functions."""

    def _load(self, fp) -> Node:
        """
        Load YAML from the given file-like object and convert it to AST.

        :param fp: A text stream to read YAML from.
        :return: Root of the constructed AST.
        """
        data = yaml.safe_load(fp)
        return Node.from_native(data)

    def _dump(self, node, fp) -> None:
        """
        Serialize the AST node to YAML and write it to the file-like object.

        :param node: The root AST node to serialize.
        :param fp: A text stream to write YAML to.
        """
        yaml.safe_dump(
            node.to_native(),
            fp,
            allow_unicode=True,
        )
