import asyncio
import base64
import subprocess
import time
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
import requests
from PIL import Image

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class DeviceManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.wda_url: Optional[str] = None
        self.session_id: Optional[str] = None
        self._http = requests.Session()
        self._wda_process: Optional[subprocess.Popen] = None

    async def connect(self):
        port = self.settings.device.wda_port
        self.wda_url = f"http://127.0.0.1:{port}"

        logger.info("Starting WebDriverAgent via tidevice...")
        self._wda_process = subprocess.Popen(
            ["tidevice", "wda", "-p", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for attempt in range(30):
            try:
                resp = requests.get(f"{self.wda_url}/status", timeout=2)
                if resp.ok:
                    logger.info("WDA ready after ~%ds", attempt)
                    break
            except requests.ConnectionError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError("WDA did not start within 30 seconds")

        resp = self._http.post(f"{self.wda_url}/session", json={
            "capabilities": {
                "alwaysMatch": {
                    "bundleId": self.settings.device.bundle_id,
                }
            }
        }, timeout=30)
        resp.raise_for_status()
        self.session_id = resp.json()["value"]["session"]
        logger.info("WDA session created: %s", self.session_id)

        caps = resp.json()["value"]["capabilities"]
        self.settings.screen.width = int(caps.get("width", self.settings.screen.width))
        self.settings.screen.height = int(caps.get("height", self.settings.screen.height))
        logger.info("Screen: %dx%d", self.settings.screen.width, self.settings.screen.height)
        return self

    async def disconnect(self):
        if self.session_id:
            try:
                self._http.delete(
                    f"{self.wda_url}/session/{self.session_id}", timeout=5
                )
            except Exception:
                pass
            self.session_id = None
        if self._wda_process:
            self._wda_process.terminate()
            self._wda_process = None
        logger.info("Disconnected")

    async def screenshot(self) -> np.ndarray:
        resp = self._http.get(
            f"{self.wda_url}/session/{self.session_id}/screenshot",
            timeout=30
        )
        resp.raise_for_status()
        png_data = base64.b64decode(resp.json()["value"])
        img = Image.open(BytesIO(png_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    async def perform_actions(self, actions: dict) -> None:
        resp = self._http.post(
            f"{self.wda_url}/session/{self.session_id}/actions",
            json=actions,
            timeout=30
        )
        resp.raise_for_status()
