import cv2
import numpy as np


def median_denoise(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply median filtering to reduce salt-and-pepper noise."""
    return cv2.medianBlur(image, kernel_size)


def gaussian_blur(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """Apply Gaussian blur to smooth the image."""
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def bilateral_filter(image: np.ndarray,diameter: int = 9,sigma_color: float = 75,sigma_space: float = 75) -> np.ndarray:
    """Apply bilateral filtering for edge-preserving noise reduction."""
    return cv2.bilateralFilter(image, diameter, sigma_color, sigma_space)