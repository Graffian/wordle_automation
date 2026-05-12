import re
from typing import List, Optional, Tuple

import cv2
import numpy as np
import pytesseract

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class OcrPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._config = "--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def extract_letter(self, tile_img: np.ndarray) -> Optional[str]:
        if tile_img.size == 0:
            return None

        processed = self._preprocess(tile_img)
        text = pytesseract.image_to_string(processed, config=self._config)
        letter = text.strip().upper()
        letter = re.sub(r"[^A-Z]", "", letter)

        if len(letter) == 1:
            return letter

        processed2 = self._preprocess_alt(tile_img)
        text2 = pytesseract.image_to_string(processed2, config=self._config)
        letter2 = text2.strip().upper()
        letter2 = re.sub(r"[^A-Z]", "", letter2)
        if len(letter2) == 1:
            return letter2

        return None

    def extract_batch(self, tiles: List[np.ndarray]) -> List[Optional[str]]:
        return [self.extract_letter(t) for t in tiles]

    def extract_grid(self, tile_images: List[List[np.ndarray]]) -> List[List[Optional[str]]]:
        return [self.extract_batch(row) for row in tile_images]

    def _preprocess(self, tile: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        resized = cv2.resize(cleaned, (56, 56), interpolation=cv2.INTER_LINEAR)
        return resized

    def _preprocess_alt(self, tile: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 128, 255, cv2.THRESH_BINARY_INV)
        resized = cv2.resize(thresh, (56, 56), interpolation=cv2.INTER_LINEAR)
        return resized
