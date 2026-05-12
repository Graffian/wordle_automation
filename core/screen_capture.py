import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class ScreenCapture:
    def __init__(self, device_mgr, settings: Settings):
        self._device = device_mgr
        self.settings = settings
        self._last_screenshot: Optional[np.ndarray] = None
        self._last_capture_time: float = 0
        self._screenshot_dir = Path(settings.screenshot_dir)
        self._screenshot_dir.mkdir(exist_ok=True)

    async def capture(self, use_cache: bool = False) -> np.ndarray:
        if use_cache and self._last_screenshot is not None:
            elapsed = time.time() - self._last_capture_time
            if elapsed < self.settings.screen.screenshot_cache_ttl:
                return self._last_screenshot

        for attempt in range(self.settings.input.max_retries):
            try:
                arr = await self._device.screenshot()
                self._last_screenshot = arr
                self._last_capture_time = time.time()
                return arr
            except Exception as e:
                logger.warning("Screenshot attempt %d failed: %s", attempt + 1, e)
                if attempt < self.settings.input.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(self.settings.input.retry_delay)
                else:
                    raise RuntimeError("Failed to capture screenshot") from e

    def save_debug(self, img: np.ndarray, name: str = "debug") -> None:
        if self.settings.debug:
            path = self._screenshot_dir / f"{name}_{int(time.time())}.png"
            cv2.imwrite(str(path), img)
            logger.debug("Saved debug image: %s", path)

    def get_screenshot_path(self, name: str = "capture") -> str:
        path = self._screenshot_dir / f"{name}_{int(time.time())}.png"
        return str(path)
