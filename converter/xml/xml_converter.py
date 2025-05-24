import re
from collections import deque
from typing import List, Tuple, Union
from xml.dom import minidom
from xml.etree.ElementTree import fromstring

from converter.ast import AST, ASTNode
from converter.converter import Converter


class XmlConverter(Converter):
    """
    Converter for XML to AST and back.

    Supports pretty-printing, tokenization, AST stripping, building,
    and unbuilding of XML documents.
    """

    NUMERIC_PATTERN = re.compile(
        r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'
    )
    BOOLEAN_LITERALS = {'true', 'false', 'null'}

    def prettify(
        self,
        text: Union[str, bytes],
        indent: int = 4
    ) -> str:
        """
        Return a pretty-printed XML string with the given indent.

        Parses the input (str or bytes) and formats it with newlines
        and indentation. Removes any empty lines in the output.
        """
        xml_bytes = text if isinstance(text, (str, bytes)) else text.encode('utf-8')
        dom = minidom.parseString(xml_bytes)
        pretty = dom.toprettyxml(indent=' ' * indent)
        # Remove empty lines
        return '\n'.join(line for line in pretty.splitlines() if line.strip())

    def _strip_text(self, xml: str) -> List[str]:
        """
        Tokenize an XML string into tags and text nodes.

        Splits on angle brackets and strips whitespace.
        """
        token_pattern = re.compile(r'<[^>]+>|[^<]+')
        return [
            token.strip()
            for token in token_pattern.findall(xml)
            if token.strip()
        ]

    def _strip_ast(self, tree: AST) -> List[str]:
        """
        Traverse the AST and generate a raw XML string.

        Returns a list containing a single string representing
        the entire XML document.
        """
        # Get the 'objects' root node
        root = tree.root.children[0]
        tokens: List[str] = []
        # Stack of tuples (node, visited_flag)
        stack: List[Tuple[ASTNode, bool]] = [(root, False)]

        while stack:
            node, visited = stack.pop()

            if not visited:
                # Container node 'objects'
                if node.tag == 'objects':
                    tokens.append('<objects>')
                    # Schedule closing tag after children
                    stack.append((node, True))
                    # Push children onto stack in reverse order
                    for child in reversed(node.children):
                        stack.append((child, False))

                # Object or array: tag name comes from attributes['key']
                elif node.tag in ('object', 'array'):
                    key = node.attributes.get('key')
                    if key:
                        tokens.append(f'<{key}>')
                        stack.append((node, True))
                    for child in reversed(node.children):
                        stack.append((child, False))

                # Leaf node: literal or string
                elif node.tag in ('literal', 'string'):
                    key = node.attributes.get('key', node.tag)
                    text = node.text or ''
                    tokens.append(f'<{key}>{text}</{key}>')

                # Ignore other tags if encountered
                else:
                    continue

            else:
                # Handle exit from container: add closing tag
                if node.tag == 'objects':
                    tokens.append('</objects>')
                elif node.tag in ('object', 'array'):
                    key = node.attributes.get('key', node.tag)
                    tokens.append(f'</{key}>')

        # Join tokens into a single string and return as a list
        return [''.join(tokens)]

    def _build(self, expressions: List[str]) -> AST:
        """
        Build an AST from raw XML string tokens.

        Parses the concatenated XML and constructs AST nodes
        for literals, strings, objects, and arrays based on
        tag structure.
        """
        self.ast = AST()
        # Create a dummy root
        root_node = self.ast.add('objects', text='ast_array')

        xml_string = ''.join(expressions)
        xml_root = fromstring(xml_string)

        queue: deque[Tuple] = deque()
        queue.append((xml_root, root_node))

        while queue:
            element, parent = queue.pop()
            children = list(element)
            text = (element.text or '').strip()
            tag = element.tag

            # Leaf element without children
            if not children and text:
                low = text.lower()
                if low in self.BOOLEAN_LITERALS or self.NUMERIC_PATTERN.fullmatch(text):
                    node_type = 'literal'
                else:
                    node_type = 'string'
                # Save the key from the tag name
                self.ast.add(
                    node_type,
                    text=text,
                    attributes={'key': tag},
                    parent=parent
                )

            # Nested elements
            elif children:
                # Count occurrences of each child tag
                counts = {}
                for c in children:
                    counts[c.tag] = counts.get(c.tag, 0) + 1

                # Array: all children share the same tag and count > 1
                if len(counts) == 1 and next(iter(counts.values())) > 1:
                    array_node = self.ast.add(
                        'array',
                        attributes={'key': tag},
                        parent=parent
                    )
                    for child in children:
                        # If an element has its own children, treat it as
                        # an object inside the array
                        if list(child):
                            obj = self.ast.add(
                                'object',
                                attributes={'key': child.tag},
                                parent=array_node
                            )
                            for gc in reversed(list(child)):
                                queue.append((gc, obj))
                        else:
                            val = (child.text or '').strip()
                            low = val.lower()
                            nt = (
                                'literal'
                                if low in self.BOOLEAN_LITERALS
                                or self.NUMERIC_PATTERN.fullmatch(val)
                                else 'string'
                            )
                            self.ast.add(
                                nt,
                                text=val,
                                attributes={'key': child.tag},
                                parent=array_node
                            )

                # Regular object
                else:
                    obj_node = self.ast.add(
                        'object',
                        attributes={'key': tag},
                        parent=parent
                    )
                    for child in reversed(children):
                        queue.append((child, obj_node))

            # Skip empty tags with no text or children
            else:
                continue

        return self.ast

    def _unbuild(self, expressions: List[str]) -> str:
        """
        Convert AST tokens back into a raw XML string.

        Call prettify() for formatted output if needed.
        """
        return ''.join(expressions)
