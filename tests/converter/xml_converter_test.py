from io import StringIO

import pytest
import xmltodict

from webutils.converter.ast import Node
from webutils.converter.xml import XmlConverter


@pytest.fixture
def converter():
    """
    Return a fresh XmlConverter instance for each test.
    """
    return XmlConverter()


def test_load_calls_parse_and_from_native(monkeypatch, converter):
    """
    _load should call xmltodict.parse on the file-like object's contents,
    then convert the resulting dict to a Node via Node.from_native.
    """
    fake_xml = '<root><a>1</a></root>'
    fake_data = {'root': {'a': '1'}}
    fake_node = object()

    monkeypatch.setattr(xmltodict, 'parse', lambda s: fake_data)
    monkeypatch.setattr(Node, 'from_native', lambda data: fake_node)

    fp = StringIO(fake_xml)
    result = converter._load(fp)

    assert result is fake_node


def test_dump_wraps_multiple_top_level_keys(monkeypatch, converter):
    """
    _dump should wrap the native dict inside a single root element if it
    contains multiple top-level keys, then call xmltodict.unparse with
    pretty=True and write the result to the provided file-like object.
    """
    native = {'a': '1', 'b': '2'}

    class DummyNode:
        def to_native(self):
            return native

    unparsed_xml = '<root><a>1</a><b>2</b></root>'
    calls = []

    monkeypatch.setattr(
        xmltodict,
        'unparse',
        lambda obj, pretty: calls.append((obj, pretty)) or unparsed_xml
    )

    fp = StringIO()
    converter._dump(DummyNode(), fp)

    # Expect the dict to be wrapped under 'root' and pretty=True
    assert calls[0][0] == {'root': native}
    assert calls[0][1] is True
    # And the output written matches the unparsed XML
    assert fp.getvalue() == unparsed_xml


def test_dump_preserves_single_root(monkeypatch, converter):
    """
    _dump should preserve the native dict as-is if it already has exactly
    one top-level key (the root), passing it directly to xmltodict.unparse.
    """
    native = {'root': {'x': 'y'}}

    class DummyNode:
        def to_native(self):
            return native

    unparsed_xml = '<root><x>y</x></root>'
    calls = []

    monkeypatch.setattr(
        xmltodict,
        'unparse',
        lambda obj, pretty: calls.append((obj, pretty)) or unparsed_xml
    )

    fp = StringIO()
    converter._dump(DummyNode(), fp)

    # Expect no additional wrapping, and pretty=True
    assert calls[0][0] == native
    assert calls[0][1] is True
    assert fp.getvalue() == unparsed_xml


def test_parse_delegates_to_load(monkeypatch, converter):
    """
    parse should accept either a raw XML string or a file-like object,
    wrap strings in StringIO, and delegate to _load.
    """
    fake_node = object()

    def fake_load(fp):
        # Ensure we received a file-like object
        assert hasattr(fp, 'read')
        return fake_node

    monkeypatch.setattr(converter, '_load', fake_load)

    # Passing a raw XML string
    out1 = converter.parse('<a />')
    assert out1 is fake_node

    # Passing an already open StringIO
    sio = StringIO('<a />')
    out2 = converter.parse(sio)
    assert out2 is fake_node


def test_read_delegates_to_dump(monkeypatch, converter):
    """
    read should delegate to _dump and return the string written to the stream.
    """
    fake_node = object()

    def fake_dump(node, fp):
        fp.write('XYZ')

    monkeypatch.setattr(converter, '_dump', fake_dump)

    res = converter.read(fake_node)
    assert res == 'XYZ'
