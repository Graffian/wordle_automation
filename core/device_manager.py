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

    async def connect(self):
        port = self.settings.device.wda_port
        self.wda_url = f"http://127.0.0.1:{port}"

        for attempt in range(30):
            try:
                resp = requests.get(f"{self.wda_url}/status", timeout=2)
                if resp.ok:
                    logger.info("WDA already reachable (attempt %d)", attempt)
                    break
            except requests.ConnectionError:
                pass
            await asyncio.sleep(1)
        else:
            raise RuntimeError("WDA did not become reachable within 30s — make sure tunneld + port forwarding are running")

        logger.info("Starting WDA session for %s ...", self.settings.device.bundle_id)
        resp = self._http.post(
            f"{self.wda_url}/session",
            json={
                "desiredCapabilities": {
                    "bundleId": self.settings.device.bundle_id,
                    "arguments": [],
                    "environment": {},
                    "shouldWaitForQuiescence": True,
                    "shouldUseTestManagerForVisibilityDetection": True,
                    "maxTypingFrequency": 60,
                    "shouldUseSingletonTestManager": False,
                }
            },
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        self.session_id = data.get("sessionId") or data.get("value", {}).get("sessionId")
        logger.info("WDA session: %s", self.session_id)

        caps = data.get("value", {}).get("capabilities", {})
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
