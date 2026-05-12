from enum import Enum
from typing import Tuple

import cv2
import numpy as np

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class TileColor(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    GRAY = "gray"
    UNKNOWN = "unknown"
    EMPTY = "empty"


class ColorRecognizer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def classify(self, tile_img: np.ndarray) -> TileColor:
        if tile_img.size == 0:
            return TileColor.EMPTY

        hsv = cv2.cvtColor(tile_img, cv2.COLOR_BGR2HSV)

        mean_hsv = cv2.mean(hsv)[:3]
        h, s, v = mean_hsv

        if v > 210 and s < 30:
            return TileColor.EMPTY

        green_mask = cv2.inRange(
            hsv,
            np.array(self.settings.colors.green_lower),
            np.array(self.settings.colors.green_upper),
        )
        yellow_mask = cv2.inRange(
            hsv,
            np.array(self.settings.colors.yellow_lower),
            np.array(self.settings.colors.yellow_upper),
        )
        gray_mask = cv2.inRange(
            hsv,
            np.array(self.settings.colors.gray_lower),
            np.array(self.settings.colors.gray_upper),
        )

        total = tile_img.shape[0] * tile_img.shape[1]
        g = cv2.countNonZero(green_mask) / total
        y = cv2.countNonZero(yellow_mask) / total
        gr = cv2.countNonZero(gray_mask) / total

        if g > 0.25:
            return TileColor.GREEN
        if y > 0.25:
            return TileColor.YELLOW
        if gr > 0.3:
            return TileColor.GRAY

        return TileColor.UNKNOWN

    def classify_batch(self, tiles: list) -> list:
        return [self.classify(t) for t in tiles]
