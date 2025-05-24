import re
from collections import deque
from typing import List
from converter.ast import AST
from converter.converter import Converter


class JsonConverter(Converter):

    def _strip_text(self, string: str) -> List[str]:
        token_pattern = re.compile(r'''
            "(?:\\.|[^"\\])*"     |  # строки
            -?\d+(?:\.\d+)?       |  # числа
            true|false|null       |  # литералы
            [{}\[\]:,]               # спец. символы
        ''', re.VERBOSE)
        return token_pattern.findall(string)

    def _strip_ast(self, tree: AST) -> List[str]:
        tokens: List[str] = []
        task = tuple

        q: deque[task] = deque()
        q.append(("enter", tree.root.children[0], None))

        while q:
            action, node, extra = q.pop()

            if action == "comma":
                tokens.append(',')
                continue

            tag = node.tag
            key = node.attributes.get('key')

            if action == "exit":
                tokens.append('}' if tag == 'object' else ']')
                continue

            if key:
                tokens.append(f'"{key}"')
                tokens.append(':')

            if tag == 'objects':
                for child in reversed(node.children):
                    q.append(("enter", child, None))

            if tag == 'object':
                tokens.append('{')
                q.append(("exit", node, None))
                for i, child in enumerate(reversed(node.children)):
                    if i > 0:
                        q.append(("comma", None, None))
                    q.append(("enter", child, None))

            elif tag == 'array':
                tokens.append('[')
                q.append(("exit", node, None))
                for i, child in enumerate(reversed(node.children)):
                    if i > 0:
                        q.append(("comma", None, None))
                    q.append(("enter", child, None))

            elif tag == 'string':
                tokens.append(f'"{node.text}"')

            elif tag == 'literal':
                tokens.append(node.text)

        return tokens

    def _build(self, expressions: List[str]) -> AST:
        # preamble
        self.ast = AST()
        self.ast.add('objects', text='ast_array')
        stack = [self.ast.root.children[-1]]
        current_key = None
        expect_key = False

        for token in expressions:
            token = token.strip()

            if token == '{':
                node = self.ast.add('object', parent=stack[-1])
                if current_key:
                    node.attributes['key'] = current_key
                    current_key = None
                stack.append(node)
                expect_key = True

            elif token == '}':
                stack.pop()
                expect_key = False

            elif token == '[':
                node = self.ast.add('array', parent=stack[-1])
                if current_key:
                    node.attributes['key'] = current_key
                    current_key = None
                stack.append(node)

            elif token == ']':
                stack.pop()

            elif token == ',':
                if stack[-1].tag == 'object':
                    expect_key = True

            elif token == ':':
                expect_key = False

            elif token.startswith('"'):
                value = token.strip('"')
                if expect_key:
                    current_key = value
                    expect_key = False
                else:
                    node = self.ast.add('string', text=value, parent=stack[-1])
                    if current_key:
                        node.attributes['key'] = current_key
                        current_key = None

            elif token in ('true', 'false', 'null') or re.match(r'-?\d+(\.\d+)?', token):
                node = self.ast.add('literal', text=token, parent=stack[-1])
                if current_key:
                    node.attributes['key'] = current_key
                    current_key = None
        return self.ast

    def _unbuild(self, expressions: List[str]) -> str:
        return ' '.join(expressions)
