from typing import Union, Optional

import cv2
import numpy as np


class QRCodeGenerator:
    """QR code generator using OpenCV."""

    def __init__(
        self,
        version: int = 0,
        correction_level: int = cv2.QRCodeEncoder_CORRECT_LEVEL_M,
        mode: int = cv2.QRCodeEncoder_MODE_AUTO,
    ) -> None:
        """
        Initialize the QR code encoder.

        Args:
            version: QR code version (1–40). 0 for auto-detection.
            correction_level: Error correction level. One of
                QRCodeEncoder_CORRECT_LEVEL_L, _M, _Q, or _H.
            mode: Encoding mode. One of
                QRCodeEncoder_MODE_AUTO, _NUMERIC, _ALPHANUMERIC,
                _BYTE, _KANJI, etc.
        """
        params = cv2.QRCodeEncoder_Params()
        params.version = version
        params.correction_level = correction_level
        params.mode = mode
        self._encoder = cv2.QRCodeEncoder_create(params)

    def generate(
        self,
        data: Union[str, bytes],
        scale: int = 10,
        output_path: Optional[str] = None,
    ) -> np.ndarray:
        """
        Generate a QR code image from the given data.

        Args:
            data: The string or bytes to encode.
            scale: Scaling factor (pixels per QR code module).
            output_path: If provided, save the image to this path.

        Returns:
            A NumPy array (BGR image) of the generated QR code.

        Raises:
            ValueError: If data is not str or bytes.
            IOError: If writing the file fails.
        """
        if isinstance(scale, str) and output_path is None:
            output_path = scale
            scale = 10

        if isinstance(data, bytes):
            text = data.decode("utf-8")
        elif isinstance(data, str):
            text = data
        else:
            raise ValueError("Data must be a string or bytes.")

        qr_matrix = self._encoder.encode(text)
        qr = np.array(qr_matrix, dtype=np.uint8)

        if scale != 1:
            height, width = qr.shape[:2]
            qr = cv2.resize(
                qr,
                dsize=(int(width * scale), int(height * scale)),
                interpolation=cv2.INTER_NEAREST,
            )

        qr_bgr = cv2.cvtColor(qr, cv2.COLOR_GRAY2BGR)

        if output_path:
            if not cv2.imwrite(output_path, qr_bgr):
                raise IOError(f"Failed to write file: {output_path}")

        return qr_bgr
