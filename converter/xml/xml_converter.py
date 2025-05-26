import xmltodict

from converter.abc_converter import Converter
from converter.ast import Node


class XmlConverter(Converter):
    """Converter for XML format using xmltodict."""

    def _load(self, fp) -> Node:
        """
        Load XML from the given text stream and convert it to AST.

        :param fp: A text stream to read XML from.
        :return: Root of the constructed AST.
        """
        raw_xml = fp.read()
        data = xmltodict.parse(raw_xml)
        return Node.from_native(data)

    def _dump(self, node, fp) -> None:
        """
        Serialize the AST node to XML and write it to the text stream.

        Wraps the document under a single root if multiple top-level
        keys exist in the native representation.

        :param node: The root AST node to serialize.
        :param fp: A text stream to write XML to.
        """
        native = node.to_native()

        # Ensure exactly one root element by wrapping if needed.
        if not (isinstance(native, dict) and len(native) == 1):
            native = {"root": native}

        xml_str = xmltodict.unparse(native, pretty=True)
        fp.write(xml_str)
