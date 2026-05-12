import base64
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
        import tidevice

        devices = tidevice.Device.list()
        if not devices:
            raise RuntimeError("No iOS devices detected via USB")
        logger.info("Detected device: %s", devices[0].udid)

        device = tidevice.Device()
        wda = tidevice.WDA(device, port=self.settings.device.wda_port)
        logger.info("Starting WebDriverAgent on device...")
        wda.start()
        self.wda_url = f"http://127.0.0.1:{self.settings.device.wda_port}"
        logger.info("WDA started at %s", self.wda_url)

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

        width = int(resp.json()["value"]["capabilities"]["width"])
        height = int(resp.json()["value"]["capabilities"]["height"])
        logger.info("Screen: %dx%d", width, height)
        self.settings.screen.width = width
        self.settings.screen.height = height
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
