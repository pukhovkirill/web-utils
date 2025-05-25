from abc import ABC, abstractmethod


class Node(ABC):
    """Abstract base class for all AST nodes."""

    @abstractmethod
    def to_native(self):
        """Convert this AST node to a native Python object."""
        raise NotImplementedError

    @staticmethod
    def from_native(data):
        """
        Recursively build an AST from a native Python object.

        :param data: A dict, list, or primitive value.
        :return: An instance of ObjectNode, ArrayNode, or ValueNode.
        """
        if isinstance(data, dict):
            return ObjectNode({
                key: Node.from_native(value)
                for key, value in data.items()
            })
        if isinstance(data, list):
            return ArrayNode([
                Node.from_native(element)
                for element in data
            ])
        return ValueNode(data)


class ObjectNode(Node):
    """
    AST node representing a mapping (dict) of string keys to nodes.

    :param members: A dict mapping string keys to Node instances.
    """

    def __init__(self, members: dict):
        self.members = members

    def to_native(self):
        """
        Convert this ObjectNode to a native dict by converting
        all member nodes.
        """
        return {
            key: node.to_native()
            for key, node in self.members.items()
        }


class ArrayNode(Node):
    """
    AST node representing a sequence (list) of nodes.

    :param elements: A list of Node instances.
    """

    def __init__(self, elements: list):
        self.elements = elements

    def to_native(self):
        """
        Convert this ArrayNode to a native list by converting
        all element nodes.
        """
        return [element.to_native() for element in self.elements]


class ValueNode(Node):
    """
    AST node representing a primitive value.

    :param value: A primitive Python value (int, float, str, bool, None).
    """

    def __init__(self, value):
        self.value = value

    def to_native(self):
        """Return the primitive value stored in this node."""
        return self.value
