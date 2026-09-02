import cv2
import numpy as np

def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple = (8, 8)) -> np.ndarray:
    """Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    enhancer = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return enhancer.apply(image)