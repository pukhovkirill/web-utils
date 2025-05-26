import cv2
import numpy as np
import pytest

from qr import QRCodeGenerator, QRCodeReader


@pytest.fixture
def generator():
    """Return a fresh QRCodeGenerator instance."""
    return QRCodeGenerator()


@pytest.fixture
def reader():
    """Return a fresh QRCodeReader instance."""
    return QRCodeReader()


def test_read_from_file(generator, reader, tmp_path):
    """Test that QRCodeReader.read() correctly reads text from a saved file."""
    text = "Hello, pytest!"
    output_file = tmp_path / "qr.png"
    # generate() now uses output_path
    _ = generator.generate(text, scale=5, output_path=str(output_file))

    decoded = reader.read(str(output_file))
    assert decoded == [text], "Should decode the same text written to file"


def test_read_from_numpy_array(generator, reader, tmp_path):
    """Test that QRCodeReader.read() accepts a NumPy array input."""
    text = "NumPy test"
    output_file = tmp_path / "qr2.png"
    generator.generate(text, scale=4, output_path=str(output_file))

    img = cv2.imread(str(output_file))
    assert img is not None, "Failed to load the generated PNG into NumPy array"

    decoded = reader.read(img)
    assert decoded == [text], "Should decode the same text from NumPy array"


def test_read_from_bytes(generator, reader, tmp_path):
    """Test that QRCodeReader.read() accepts raw PNG bytes."""
    text = "Bytes test"
    output_file = tmp_path / "qr3.png"
    generator.generate(text, scale=3, output_path=str(output_file))

    with open(output_file, "rb") as f:
        data = f.read()

    decoded = reader.read(data)
    assert decoded == [text], "Should decode the same text from raw bytes"


def test_invalid_file_path(reader):
    """Test that reading from a non-existent file path raises IOError."""
    with pytest.raises(IOError) as excinfo:
        reader.read("nonexistent_file.png")
    msg = str(excinfo.value)
    assert "Cannot open image file" in msg, "Expected IOError about opening image file"


def test_invalid_bytes(reader):
    """Test that reading from invalid byte content raises IOError."""
    with pytest.raises(IOError) as excinfo:
        reader.read(b"\x00\x01\x02")
    msg = str(excinfo.value)
    assert "Cannot decode image from bytes" in msg, "Expected IOError about decoding from bytes"


def test_unsupported_type(reader):
    """Test that reading from an unsupported type raises IOError."""
    with pytest.raises(IOError):
        reader.read(12345)


def test_mock_detect_and_decode(monkeypatch, reader):
    """Test that read() filters out empty strings from detector output."""
    class DummyDetector:
        def detectAndDecodeMulti(self, img):
            # Returns (retval, decoded_list, points, straight_qrcode)
            return None, ["A", "", "B"], None, None

    monkeypatch.setattr(reader, "detector", DummyDetector())
    dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)

    result = reader.read(dummy_img)
    assert result == ["A", "B"], "Empty strings should be filtered out of decoded results"
