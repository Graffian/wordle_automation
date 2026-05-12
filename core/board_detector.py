from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class BoardDetector:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._cached_grid: Optional[List[List[Tuple[int, int, int, int]]]] = None
        self._cached_letters: Optional[List[List[str]]] = None

    def detect_grid(
        self, screenshot: np.ndarray
    ) -> List[List[Tuple[int, int, int, int]]]:
        h, w = screenshot.shape[:2]

        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(
            blurred, self.settings.board.canny_low, self.settings.board.canny_high
        )

        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        tiles = []
        for cnt in contours:
            x, y, tw, th = cv2.boundingRect(cnt)
            aspect = tw / th
            area = tw * th
            if (
                self.settings.board.tile_aspect_min
                < aspect
                < self.settings.board.tile_aspect_max
                and self.settings.board.tile_area_min < area < self.settings.board.tile_area_max
            ):
                tiles.append((x, y, tw, th))

        if len(tiles) >= self.settings.board.min_tiles_for_auto:
            return self._cluster_into_grid(tiles, h, w)
        else:
            logger.info(
                "Found %d tiles, using ratio-based fallback", len(tiles)
            )
            return self._ratio_grid(h, w)

    def get_manual_centers(self) -> List[List[Tuple[int, int]]]:
        return self.settings.board.tile_centers

    def centers_to_bbox(
        self, centers: List[List[Tuple[int, int]]], tile_size: int = 60
    ) -> List[List[Tuple[int, int, int, int]]]:
        grid = []
        for row in centers:
            row_bbox = []
            for cx, cy in row:
                x = cx - tile_size // 2
                y = cy - tile_size // 2
                row_bbox.append((x, y, tile_size, tile_size))
            grid.append(row_bbox)
        return grid

    def _cluster_into_grid(
        self, tiles: List[Tuple[int, int, int, int]], h: int, w: int
    ) -> List[List[Tuple[int, int, int, int]]]:
        tiles.sort(key=lambda t: (t[1], t[0]))

        rows = []
        current_row = []
        last_y = -100
        for t in tiles:
            x, y, tw, th = t
            if abs(y - (last_y + th // 2)) > th // 2 and current_row:
                current_row.sort(key=lambda t: t[0])
                rows.append(current_row)
                current_row = [t]
                last_y = y
            else:
                current_row.append(t)
                last_y = (
                    sum(t[1] + t[3] // 2 for t in current_row) // len(current_row)
                )
        if current_row:
            current_row.sort(key=lambda t: t[0])
            rows.append(current_row)

        expected = self.settings.board.rows
        if len(rows) >= expected:
            rows = rows[:expected]
            for i in range(len(rows)):
                rows[i] = rows[i][: self.settings.board.cols]

        logger.info("Detected %dx%d grid", len(rows), len(rows[0]) if rows else 0)
        return rows

    def _ratio_grid(
        self, h: int, w: int
    ) -> List[List[Tuple[int, int, int, int]]]:
        rows = self.settings.board.rows
        cols = self.settings.board.cols
        grid_w = int(w * self.settings.board.grid_width_ratio)
        grid_left = (w - grid_w) // 2
        grid_top = int(h * self.settings.board.grid_top_ratio)
        tile_w = grid_w // cols
        tile_h = tile_w
        gap = 4

        grid = []
        for row in range(rows):
            row_tiles = []
            for col in range(cols):
                x = grid_left + col * (tile_w + gap)
                y = grid_top + row * (tile_h + gap)
                row_tiles.append((x, y, tile_w, tile_h))
            grid.append(row_tiles)

        return grid

    def extract_tile(
        self, screenshot: np.ndarray, tile_coords: Tuple[int, int, int, int]
    ) -> np.ndarray:
        x, y, tw, th = tile_coords
        pad = 2
        y1 = max(0, y - pad)
        y2 = min(screenshot.shape[0], y + th + pad)
        x1 = max(0, x - pad)
        x2 = min(screenshot.shape[1], x + tw + pad)
        return screenshot[y1:y2, x1:x2]

    def get_tile_center(
        self, tile_coords: Tuple[int, int, int, int]
    ) -> Tuple[int, int]:
        x, y, tw, th = tile_coords
        return (x + tw // 2, y + th // 2)

    def get_adjacent_indices(
        self, row: int, col: int
    ) -> List[Tuple[int, int]]:
        dirs = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ]
        result = []
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.settings.board.rows and 0 <= nc < self.settings.board.cols:
                result.append((nr, nc))
        return result
