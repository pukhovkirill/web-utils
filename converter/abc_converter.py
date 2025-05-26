from abc import ABC, abstractmethod
from io import StringIO
from typing import Union, TextIO

from converter.ast import Node


class Converter(ABC):
    """Abstract base class for format converters.

    Provides a unified interface for parsing a source string or stream
    into an AST and serializing an AST back to a string.
    """

    def parse(self, src: Union[str, StringIO]) -> Node:
        """Parse the source string or stream into an AST Node."""
        stream = StringIO(src) if isinstance(src, str) else src
        return self._load(stream)

    def read(self, node: Node) -> str:
        """Serialize the AST Node back to a string."""
        stream = StringIO()
        self._dump(node, stream)
        return stream.getvalue()

    @abstractmethod
    def _load(self, fp: TextIO) -> Node:
        """Read from the file-like object and return the root AST Node."""
        ...

    @abstractmethod
    def _dump(self, node: Node, fp: TextIO) -> None:
        """Serialize the AST Node into the file-like object."""
        ...
