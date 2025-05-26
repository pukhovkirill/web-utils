from io import StringIO
from unittest.mock import patch, MagicMock

import pytest

from converter.ast import Node, ArrayNode
from converter.csv import CsvConverter


@pytest.fixture
def converter():
    """
    Return a fresh CsvConverter instance for each test.
    """
    return CsvConverter()


def test_load_empty_csv_returns_empty_array_node(converter):
    """
    _load should return an empty ArrayNode when given an empty CSV
    with no header or rows.
    """
    csv_data = ""  # without header or rows
    node = converter._load(StringIO(csv_data))
    assert isinstance(node, ArrayNode)
    assert node.to_native() == []


def test_load_csv_parses_header_and_rows(converter):
    """
    _load should parse the header and subsequent rows correctly,
    converting them into an ArrayNode of dictionaries.
    """
    csv_data = "a,b\n1,2\n3,4\n"
    node = converter._load(StringIO(csv_data))
    expected = [
        {'a': '1', 'b': '2'},
        {'a': '3', 'b': '4'}
    ]
    assert node.to_native() == expected


def test_parse_wraps_str_and_delegates_to_load(converter, monkeypatch):
    """
    parse should accept either a string or a file-like object,
    wrap strings in a StringIO, and delegate to _load.
    """
    fake_node = Node.from_native([{'x': 'y'}])

    def fake_load(fp):
        # fp should be a text stream
        assert hasattr(fp, 'read')
        return fake_node

    monkeypatch.setattr(converter, '_load', fake_load)

    # passing a raw string
    result1 = converter.parse("foo,bar")
    assert result1 is fake_node

    # passing a StringIO
    sio = StringIO("foo,bar")
    result2 = converter.parse(sio)
    assert result2 is fake_node


def test_dump_raises_on_empty_list(converter):
    """
    _dump should raise a ValueError when given an ArrayNode
    containing an empty list.
    """
    empty_node = Node.from_native([])
    with pytest.raises(ValueError) as excinfo:
        converter._dump(empty_node, StringIO())
    assert "non-empty list of dicts" in str(excinfo.value)


def test_dump_writes_header_and_rows(monkeypatch, converter):
    """
    _dump should write the CSV header before writing any rows,
    using csv.DictWriter with the correct fieldnames.
    """
    native_list = [{'a': '1', 'b': '2'}]
    node = Node.from_native(native_list)

    mock_writer = MagicMock()
    # Patch DictWriter call and check arguments
    with patch('csv.DictWriter', return_value=mock_writer) as mock_dw:
        fp = StringIO()
        converter._dump(node, fp)

        # verify that DictWriter was called with the same file pointer and correct fieldnames
        mock_dw.assert_called_once_with(fp, fieldnames=['a', 'b'])
        # verify that header is written first, then rows
        mock_writer.writeheader.assert_called_once_with()
        mock_writer.writerows.assert_called_once_with(native_list)


def test_read_delegates_to_dump(converter, monkeypatch):
    """
    read should delegate to _dump and return the resulting string.
    """
    fake_node = Node.from_native([{'foo': 'bar'}])
    calls = []

    def fake_dump(node, fp):
        calls.append((node, fp))
        fp.write("OUTPUT")

    monkeypatch.setattr(converter, '_dump', fake_dump)

    result = converter.read(fake_node)
    # result is what fake_dump wrote
    assert result == "OUTPUT"
    # dump was called exactly once with that node
    assert calls and calls[0][0] is fake_node
