import asyncio
import base64
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from appium.webdriver.webdriver import WebDriver

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class ScreenCapture:
    def __init__(self, driver: WebDriver, settings: Settings):
        self.driver = driver
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
                raw = self.driver.get_screenshot_as_png()
                img = Image.open(BytesIO(raw))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                arr = np.array(img)
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
                self._last_screenshot = arr
                self._last_capture_time = time.time()
                return arr
            except Exception as e:
                logger.warning("Screenshot attempt %d failed: %s", attempt + 1, e)
                if attempt < self.settings.input.max_retries - 1:
                    await asyncio.sleep(self.settings.input.retry_delay)
                else:
                    raise RuntimeError("Failed to capture screenshot") from e

    def capture_sync(self, use_cache: bool = False) -> np.ndarray:
        if use_cache and self._last_screenshot is not None:
            elapsed = time.time() - self._last_capture_time
            if elapsed < self.settings.screen.screenshot_cache_ttl:
                return self._last_screenshot

        raw = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(raw))
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        self._last_screenshot = arr
        self._last_capture_time = time.time()
        return arr

    def save_debug(self, img: np.ndarray, name: str = "debug") -> None:
        if self.settings.debug:
            path = self._screenshot_dir / f"{name}_{int(time.time())}.png"
            cv2.imwrite(str(path), img)
            logger.debug("Saved debug image: %s", path)

    def get_screenshot_path(self, name: str = "capture") -> str:
        path = self._screenshot_dir / f"{name}_{int(time.time())}.png"
        return str(path)
