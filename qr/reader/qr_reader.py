import numpy as np
from typing import List, Union
import cv2


class QRCodeReader:
    """
    Reader for extracting QR codes from images using OpenCV.
    """

    def __init__(self) -> None:
        self.detector = cv2.QRCodeDetector()

    def read(self, image: Union[str, np.ndarray, bytes]) -> List[str]:
        """
        Read and decode all QR codes from the given image.

        Args:
            image: Path to an image file, raw image bytes,
                   or a NumPy array (OpenCV image).

        Returns:
            A list of decoded QR code strings. If no QR codes
            are found, returns an empty list.

        Raises:
            IOError: If the image cannot be opened or decoded.
        """
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise IOError(f"Cannot open image file: {image}")
        elif isinstance(image, (bytes, bytearray)):
            arr = np.frombuffer(image, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise IOError("Cannot decode image from bytes")
        elif isinstance(image, np.ndarray):
            img = image
        else:
            raise IOError("Unsupported image type")

        texts = self.detector.detectAndDecodeMulti(img)[1]
        return [t for t in texts if t]
