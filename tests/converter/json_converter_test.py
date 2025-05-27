import json
from io import StringIO

import pytest

from webutils.converter.ast import Node
from webutils.converter.json import JsonConverter


@pytest.fixture
def converter():
    """
    Return a fresh JsonConverter instance for each test.
    """
    return JsonConverter()


def test_load_calls_json_load_and_from_native(monkeypatch, converter):
    """
    _load should call json.load on the file-like object and then
    use Node.from_native to convert the loaded data into a Node.
    """
    # Prepare fake return values
    fake_data = {'a': 1, 'b': [2, 3]}
    fake_node = object()

    # Monkey-patch json.load and Node.from_native
    monkeypatch.setattr(json, 'load', lambda fp: fake_data)
    monkeypatch.setattr(Node, 'from_native', lambda data: fake_node)

    fp = StringIO('{"a":1,"b":[2,3]}')
    result = converter._load(fp)

    assert result is fake_node


def test_dump_calls_json_dump_with_correct_args(monkeypatch, converter):
    """
    _dump should call json.dump with the node's native data,
    writing to the provided file-like object, with ensure_ascii=False
    and indent=2.
    """
    native = {'x': 'y'}
    fake_node = Node.from_native(native)
    fp = StringIO()

    calls = []

    def fake_dump(obj, fp_arg, ensure_ascii, indent):
        calls.append((obj, fp_arg, ensure_ascii, indent))

    # Monkey-patch json.dump
    monkeypatch.setattr(json, 'dump', fake_dump)

    converter._dump(fake_node, fp)

    assert calls == [(native, fp, False, 2)]


def test_parse_delegates_to_load(monkeypatch, converter):
    """
    parse should accept either a raw JSON string or a file-like object,
    wrap a string in StringIO if needed, and delegate to _load.
    """
    fake_node = object()

    def fake_load(fp):
        # Ensure we received a file-like object
        assert hasattr(fp, 'read')
        return fake_node

    monkeypatch.setattr(converter, '_load', fake_load)

    # Passing a raw string
    out1 = converter.parse('{"k":123}')
    assert out1 is fake_node

    # Passing an already open StringIO
    sio = StringIO('{"k":123}')
    out2 = converter.parse(sio)
    assert out2 is fake_node


def test_read_delegates_to_dump(monkeypatch, converter):
    """
    read should delegate to _dump and return the written string.
    """
    fake_node = object()

    def fake_dump(node, fp):
        # Write directly to the stream what should be returned
        fp.write('RESULT')

    monkeypatch.setattr(converter, '_dump', fake_dump)

    res = converter.read(fake_node)
    assert res == 'RESULT'


def test_round_trip_serialization(converter):
    """
    Ensure that parsing the output of read on a node restores
    the original native structure.
    """
    orig = {'num': 42, 'items': ['a', 'b']}
    # Serialize to string
    dumped = converter.read(Node.from_native(orig))
    # Parse back to a node
    node2 = converter.parse(dumped)
    assert node2.to_native() == orig
