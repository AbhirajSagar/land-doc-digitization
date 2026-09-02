import cv2
import numpy as np

def upscale_image(image: np.ndarray, scale: float = 2.0) -> np.ndarray:
    """Upscale image resolution using bicubic interpolation."""
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)   