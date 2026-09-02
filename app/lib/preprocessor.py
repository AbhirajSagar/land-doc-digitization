from pathlib import Path
from typing import Union
import cv2
import numpy as np

from app.lib.contrast import enhance_contrast
from app.lib.denoising import median_denoise
from app.lib.grayscale import to_grayscale
from app.lib.upscaling import upscale_image

def preprocess(image: np.ndarray, output_dir: Union[str, Path] = "output") -> np.ndarray:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    upscaled_image = upscale_image(image)
    cv2.imwrite(str(output_path / "01_upscaled.png"), upscaled_image)

    grayscale_image = to_grayscale(upscaled_image)
    cv2.imwrite(str(output_path / "02_grayscale.png"), grayscale_image)

    denoised_image = median_denoise(grayscale_image)
    cv2.imwrite(str(output_path / "03_denoised.png"), denoised_image)

    contrast_enhanced_image = enhance_contrast(denoised_image)
    cv2.imwrite(str(output_path / "04_contrast_enhanced.png"), contrast_enhanced_image)

    return str(output_path / "04_contrast_enhanced.png")