import cv2
import numpy as np


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert an image to single-channel grayscale."""
    if len(image.shape) == 2:
        return image
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)