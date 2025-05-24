from collections import deque
from converter.ast import AST
from converter.converter import Converter
from typing import List


class CsvConverter(Converter):
    def _strip_text(self, string: str) -> List[List[str]]:
        lines = string.strip().splitlines()
        return [line.strip().split(',') for line in lines]

    def _build(self, expressions: List[List[str]]) -> AST:
        self.ast = AST()
        ast_array = self.ast.add('objects', text='ast_array', parent=self.ast.root)
        header = expressions[0]

        for row in expressions[1:]:
            obj_node = self.ast.add('object', parent=ast_array)
            for key, value in zip(header, row):
                value = value.strip()
                if ';' in value:
                    arr_node = self.ast.add('array', parent=obj_node, attributes={'key': key})
                    for item in value.split(';'):
                        tag = 'literal' if item.replace('.', '', 1).isdigit() else 'string'
                        self.ast.add(tag, text=item.strip(), parent=arr_node)
                else:
                    tag = 'literal' if value.replace('.', '', 1).isdigit() else 'string'
                    self.ast.add(tag, text=value, parent=obj_node, attributes={'key': key})

        return self.ast

    def _strip_ast(self, tree: AST) -> List[List[str]]:
        rows = []
        header = []

        task = tuple

        q: deque[task] = deque()
        q.append(("objects", tree.root.children[0]))

        while q:
            tag, node = q.pop()

            if node.tag == 'objects':
                for child in node.children:
                    q.append((child.tag, child))

            elif tag == 'object':
                row_dict = {}
                for child in node.children:
                    key = child.attributes.get('key')
                    if child.tag == 'array':
                        val = ';'.join(grandchild.text for grandchild in child.children)
                    else:
                        val = child.text or ''
                    row_dict[key] = val
                    if key and key not in header:
                        header.append(key)
                rows.append([row_dict.get(k, '') for k in header])

            else:
                pass

        return [header] + rows

    def _unbuild(self, expressions: List[List[str]]) -> str:
        return '\n'.join([','.join(row) for row in expressions])
