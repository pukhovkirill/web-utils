from typing import List


class ASTNode:
    def __init__(self, tag, attributes=None, text=None):
        self.tag = tag
        self.attributes = attributes if attributes else {}
        self.text = text
        self.children: List[ASTNode] = []

    def add_child(self, child):
        self.children.append(child)


class AST:
    def __init__(self):
        self.root = ASTNode('root')
        self._stack = [self.root]

    def add(self, tag, attributes=None, text=None, parent=None) -> ASTNode:
        node = ASTNode(tag, attributes, text)
        if parent is None:
            self.root.add_child(node)
        else:
            parent.add_child(node)
        return node

    def __iter__(self):
        self._stack = [self.root]
        return self

    def __next__(self) -> ASTNode:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        self._stack.extend(reversed(node.children))
        return node
