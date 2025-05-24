import json
import re
from collections import deque
from typing import List, Optional, Tuple

from converter.ast import AST, ASTNode
from converter.converter import Converter


class JsonConverter(Converter):
    """
    Converter for JSON with pretty-printing, tokenization, AST stripping,
    rebuilding, and unbuilding.
    """

    NUMERIC_PATTERN = re.compile(
        r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    )

    def prettify(self, text: str, indent: int = 4) -> str:
        """
        Return a pretty-printed JSON string with the given indent.

        If `text` is already a Python dict or list, it is used directly.
        Otherwise, it is parsed from a JSON string first.
        """
        obj = text if isinstance(text, (dict, list)) else json.loads(text)
        return json.dumps(obj, indent=indent)

    def _strip_text(self, string: str) -> List[str]:
        """
        Tokenize a JSON string into tokens: strings, numbers (with exponent),
        booleans, nulls, braces, brackets, colons, and commas.
        """
        token_pattern = re.compile(
            r'''
            "(?:\\.|[^"\\])*"         |  # double-quoted strings
            -?\d+(?:\.\d+)?           # integers and decimals
            (?:[eE][+-]?\d+)?         |  # optional exponent
            true|false|null           |  # boolean literals and null
            [{}\[\]:,]                   # special JSON characters
            ''',
            re.VERBOSE
        )
        return token_pattern.findall(string)

    def _strip_ast(self, tree: AST) -> List[str]:
        """
        Traverse an AST and convert it into a flat list of JSON tokens.
        """
        tokens: List[str] = []
        queue: deque[Tuple[str, Optional[ASTNode]]] = deque()
        queue.append(('enter', tree.root.children[0]))

        while queue:
            action, node = queue.pop()

            if action == 'comma':
                tokens.append(',')
                continue

            tag = node.tag if node else ''
            key = node.attributes.get('key') if node else None

            if action == 'exit':
                tokens.append('}' if tag == 'object' else ']')
                continue

            if key and key != 'item':
                tokens.extend([f'"{key}"', ':'])

            if tag == 'objects':
                tokens.append('{')
                queue.append(('exit', ASTNode('object')))
                for child in reversed(node.children):
                    queue.append(('enter', child))

            elif tag == 'object':
                if node.attributes:
                    tokens.append('{')
                    queue.append(('exit', node))
                for i, child in enumerate(reversed(node.children)):
                    if i:
                        queue.append(('comma', None))
                    queue.append(('enter', child))

            elif tag == 'array':
                tokens.append('[')
                queue.append(('exit', node))
                for i, child in enumerate(reversed(node.children)):
                    if i:
                        queue.append(('comma', None))
                    queue.append(('enter', child))

            elif tag == 'string':
                tokens.append(f'"{node.text}"')

            elif tag == 'literal':
                tokens.append(node.text)

        return tokens

    def _build(self, expressions: List[str]) -> AST:
        """
        Build an AST from a list of JSON tokens.
        """
        self.ast = AST()
        self.ast.add('objects', text='ast_array')
        stack: List[ASTNode] = [self.ast.root.children[0]]
        current_key: Optional[str] = None
        expect_key = False

        for token in expressions:
            token = token.strip()

            if token == '{':
                node = self.ast.add('object', parent=stack[-1])
                if current_key is not None:
                    node.attributes['key'] = current_key
                    current_key = None
                stack.append(node)
                expect_key = True

            elif token == '}':
                stack.pop()
                expect_key = False

            elif token == '[':
                node = self.ast.add('array', parent=stack[-1])
                if current_key is not None:
                    node.attributes['key'] = current_key
                    current_key = None
                stack.append(node)
                expect_key = False

            elif token == ']':
                stack.pop()
                expect_key = False

            elif token == ',':
                if stack[-1].tag == 'object':
                    expect_key = True

            elif token == ':':
                expect_key = False

            elif token.startswith('"') and token.endswith('"'):
                value = token[1:-1]
                if expect_key:
                    current_key = value
                    expect_key = False
                else:
                    node = self.ast.add(
                        'string', text=value, parent=stack[-1]
                    )
                    if current_key is not None:
                        node.attributes['key'] = current_key
                        current_key = None

            elif token in ('true', 'false', 'null') or \
                    self.NUMERIC_PATTERN.fullmatch(token):
                node = self.ast.add(
                    'literal', text=token, parent=stack[-1]
                )
                if current_key is not None:
                    node.attributes['key'] = current_key
                    current_key = None
                expect_key = False

        return self.ast

    def _unbuild(self, expressions: List[str]) -> str:
        """
        Convert a list of tokens back into a compact JSON string without
        unnecessary whitespace.
        """
        return ''.join(expressions)
