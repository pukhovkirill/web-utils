from abc import ABC, abstractmethod
from typing import List

from .ast import AST


class Converter(ABC):

    def parse_text(self, text) -> AST:
        expressions = self._strip_text(text)
        return self._build(expressions)

    def read_tree(self, tree: AST) -> str:
        expressions = self._strip_ast(tree)
        return self._unbuild(expressions)

    @abstractmethod
    def _strip_text(self, string: str) -> List[str]:
        ...

    @abstractmethod
    def _strip_ast(self, tree: AST) -> List[str]:
        ...

    @abstractmethod
    def _build(self, expressions: List[str]) -> AST:
        ...

    @abstractmethod
    def _unbuild(self, expressions: List[str]) -> str:
        ...
