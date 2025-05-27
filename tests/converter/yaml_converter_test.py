from io import StringIO

import pytest
import yaml

from webutils.converter.ast import Node
from webutils.converter.yaml import YamlConverter


@pytest.fixture
def converter():
    """
    Return a fresh YamlConverter instance for each test.
    """
    return YamlConverter()


def test_load_calls_yaml_safe_load_and_from_native(monkeypatch, converter):
    """
    _load should call yaml.safe_load on the provided file-like object,
    and then convert the resulting native data to a Node via Node.from_native.
    """
    fake_data = {'a': 1, 'b': [2, 3]}
    fake_node = object()
    monkeypatch.setattr(yaml, 'safe_load', lambda fp: fake_data)
    monkeypatch.setattr(Node, 'from_native', lambda data: fake_node)

    fp = StringIO("a: 1\nb:\n  - 2\n  - 3\n")
    result = converter._load(fp)
    assert result is fake_node


def test_dump_calls_yaml_safe_dump_with_correct_args(monkeypatch, converter):
    """
    _dump should call yaml.safe_dump with:
      1. the node’s native data,
      2. the provided file-like object,
      3. allow_unicode=True,
    and write the dump output into the stream.
    """
    native = {'x': 'y', 'list': [1, 2]}

    class DummyNode:
        def to_native(self):
            return native

    node = DummyNode()
    fp = StringIO()
    calls = []

    def fake_safe_dump(data, fp_arg, allow_unicode):
        calls.append((data, fp_arg, allow_unicode))
        fp_arg.write("DUMPED")

    monkeypatch.setattr(yaml, 'safe_dump', fake_safe_dump)

    converter._dump(node, fp)

    assert calls == [(native, fp, True)]
    assert fp.getvalue() == "DUMPED"


def test_parse_delegates_to_load(monkeypatch, converter):
    """
    parse should accept either a YAML string or a file-like object,
    wrap strings in StringIO, and delegate to _load.
    """
    fake_node = object()

    def fake_load(fp):
        # Ensure we received a file-like object
        assert hasattr(fp, 'read')
        return fake_node

    monkeypatch.setattr(converter, '_load', fake_load)

    # Passing a raw YAML string
    assert converter.parse("key: value") is fake_node

    # Passing an already open StringIO
    sio = StringIO("key: value")
    assert converter.parse(sio) is fake_node


def test_read_delegates_to_dump(monkeypatch, converter):
    """
    read should delegate to _dump and return the string written to the stream.
    """
    fake_node = object()

    def fake_dump(node, fp):
        fp.write("RESULT")

    monkeypatch.setattr(converter, '_dump', fake_dump)

    assert converter.read(fake_node) == "RESULT"
