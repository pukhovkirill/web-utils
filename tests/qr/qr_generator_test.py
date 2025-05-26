import cv2
import numpy as np
import pytest

from qr import QRCodeGenerator


@pytest.fixture
def generator():
    """Create a QRCodeGenerator instance for testing."""
    return QRCodeGenerator()


def test_generate_returns_numpy_array(generator):
    """Test that generate() returns a NumPy array with 3 BGR channels and correct dimensions."""
    img = generator.generate("test data", scale=5)
    assert isinstance(img, np.ndarray), "Should return a NumPy array"
    h, w, c = img.shape
    assert c == 3, "There should be 3 channels (BGR)"
    assert h == w, "Width and height of the QR code should be equal"
    assert h % 5 == 0, "Size should be a multiple of the scale factor"


def test_generate_with_bytes_input(generator):
    """Test that generate() accepts bytes input and returns a NumPy array."""
    data = "Hello, world!".encode('utf-8')
    img = generator.generate(data, scale=3)
    assert isinstance(img, np.ndarray), "Should return an array for bytes input"
    _, _, c = img.shape
    assert c == 3, "There should be 3 channels (BGR)"


def test_scale_changes_size(generator):
    """Test that increasing the scale factor increases the output image size."""
    img_small = generator.generate("X", scale=2)
    img_large = generator.generate("X", scale=7)
    assert img_large.shape[0] > img_small.shape[0], "Larger scale should produce a larger QR code"


def test_save_to_file(generator, tmp_path):
    """Test that generate() saves the QR code to a file when output_path is provided."""
    out_file = tmp_path / "qrcode.png"
    img = generator.generate("file test", scale=4, output_path=str(out_file))
    assert out_file.exists(), "File should be created"
    loaded = cv2.imread(str(out_file))
    assert loaded is not None, "Created file should be readable"
    np.testing.assert_array_equal(img, loaded)


def test_invalid_data_type_raises(generator):
    """Test that generate() raises ValueError for unsupported data types."""
    with pytest.raises(ValueError):
        generator.generate(12345)  # not str or bytes
