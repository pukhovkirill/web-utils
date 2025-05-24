import re
from collections import deque
from typing import List, Tuple

from converter.ast import AST, ASTNode
from converter.converter import Converter


class YamlConverter(Converter):
    """
    Converter for YAML text to AST and back.

    Parses indented YAML lines into an AST and serializes ASTs back to
    YAML with configurable indent width. Supports numeric, boolean,
    and null literal detection.
    """

    # Configurable indent width (default: 2 spaces)
    INDENT_WIDTH: int = 2

    # Pattern for numeric literals: integers, decimals, and exponent notation
    NUMERIC_PATTERN = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?')

    # Literals to recognize as boolean or null
    BOOLEAN_LITERALS = {'true', 'false', 'null'}

    def _strip_text(self, text: str) -> List[str]:
        """
        Split YAML string into non-empty lines, preserving indentation.

        Strips trailing whitespace and ignores blank lines.
        """
        return [
            line.rstrip()
            for line in text.strip().splitlines()
            if line.strip()
        ]

    def _build(self, lines: List[str]) -> AST:
        """
        Build an AST from indented YAML lines.

        - Lines with zero indent start new top-level objects.
        - Lines starting with "- " are list items.
        - "key: value" pairs create literal or string nodes.
        - "key:" without value starts a nested array.
        """
        self.ast = AST()
        root = self.ast.add('objects', text='ast_array')
        stack: List[Tuple[ASTNode, int]] = [(root, -1)]

        for line in lines:
            indent = len(line) - len(line.lstrip())
            level = indent // self.INDENT_WIDTH
            content = line.strip()

            # Ascend to correct parent level
            while stack and stack[-1][1] >= level:
                stack.pop()
            parent = stack[-1][0]

            # Top-level object
            if indent == 0:
                key = content.partition(':')[0].strip()
                obj = self.ast.add(
                    'object',
                    attributes={'key': key},
                    parent=parent
                )
                stack.append((obj, level))
                continue

            # List item
            if content.startswith('- '):
                value = content[2:].strip()
                # Find or create the array node
                if parent.tag == 'array':
                    array_node = parent
                elif parent.children and parent.children[-1].tag == 'array':
                    array_node = parent.children[-1]
                else:
                    pkey = parent.attributes.get('key')
                    attrs = {'key': pkey} if pkey is not None else {}
                    array_node = self.ast.add(
                        'array',
                        attributes=attrs,
                        parent=parent
                    )
                    stack.append((array_node, level))

                # Always treat list items as strings
                self.ast.add(
                    'string',
                    text=value,
                    parent=array_node
                )
                continue

            # "key: value" or start of nested list
            if ':' in content:
                key, _, val = content.partition(':')
                key = key.strip()
                val = val.strip()

                if val:
                    low = val.lower()
                    if (
                        self.NUMERIC_PATTERN.fullmatch(val)
                        or low in self.BOOLEAN_LITERALS
                    ):
                        tag = 'literal'
                    else:
                        tag = 'string'
                    self.ast.add(
                        tag,
                        text=val,
                        attributes={'key': key},
                        parent=parent
                    )
                else:
                    # Start nested array under this key
                    array_node = self.ast.add(
                        'array',
                        attributes={'key': key},
                        parent=parent
                    )
                    stack.append((array_node, level))

        return self.ast

    def _strip_ast(self, tree: AST) -> List[str]:
        """
        Convert an AST back into indented YAML lines.

        - 'object' nodes produce "key:" lines.
        - 'array' nodes produce a key header (if present) and "- item" lines.
        - 'literal' and 'string' nodes produce "key: value" lines.
        """
        lines: List[str] = []
        queue: deque[Tuple[ASTNode, int]] = deque([
            (tree.root.children[0], 0)
        ])

        while queue:
            node, level = queue.popleft()
            prefix = ' ' * (self.INDENT_WIDTH * level)

            if node.tag == 'objects':
                for child in reversed(node.children):
                    queue.append((child, level))
                continue

            if node.tag == 'object':
                key = node.attributes.get('key', node.tag)
                lines.append(f"{prefix}{key}:")
                for child in reversed(node.children):
                    queue.appendleft((child, level + 1))

            elif node.tag == 'array':
                key = node.attributes.get('key')
                if key:
                    lines.append(f"{prefix}{key}:")
                for child in node.children:
                    text = child.text or ''
                    lines.append(f"{prefix}- {text}")

            else:  # literal or string
                key = node.attributes.get('key')
                text = node.text or ''
                if key:
                    lines.append(f"{prefix}{key}: {text}")
                else:
                    lines.append(f"{prefix}- {text}")

        return lines

    def _unbuild(self, lines: List[str]) -> str:
        """
        Join YAML lines into a single string with newline separators.
        """
        return '\n'.join(lines)
