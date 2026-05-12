import asyncio
import time
from typing import Optional

import subprocess
from appium import webdriver
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class DeviceManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.driver: Optional[WebDriver] = None
        self.device_udid: Optional[str] = None

    def detect_device(self) -> str:
        result = subprocess.run(
            ["idevice_id", "-l"],
            capture_output=True, text=True, timeout=10
        )
        udids = result.stdout.strip().splitlines()
        if not udids:
            raise RuntimeError("No iOS devices detected via USB. Check cable and libimobiledevice.")
        self.device_udid = udids[0]
        logger.info("Detected device UDID: %s", self.device_udid)
        return self.device_udid

    def ensure_wda_running(self) -> None:
        if self.device_udid:
            logger.info("Checking WebDriverAgent...")
            result = subprocess.run(
                ["ideviceinfo", "-u", self.device_udid, "-k", "DeviceName"],
                capture_output=True, text=True, timeout=10
            )
            logger.info("Device name: %s", result.stdout.strip())

    async def connect(self) -> WebDriver:
        if not self.device_udid:
            self.detect_device()
        self.ensure_wda_running()

        desired_caps = {
            "platformName": self.settings.appium.platform_name,
            "appium:platformVersion": self.settings.appium.platform_version,
            "appium:deviceName": self.settings.appium.device_name,
            "appium:udid": self.device_udid,
            "appium:automationName": self.settings.appium.automation_name,
            "appium:bundleId": self.settings.appium.bundle_id,
            "appium:noReset": self.settings.appium.no_reset,
            "appium:fullReset": self.settings.appium.full_reset,
            "appium:usePrebuiltWDA": self.settings.appium.use_prebuilt_wda,
            "appium:wdaBundleId": self.settings.appium.wda_bundle_id,
            "appium:wdaLocalPort": self.settings.appium.wda_port,
            "appium:shouldUseSingletonTestManager": False,
            "appium:waitForIdleTimeout": 5,
        }

        logger.info("Connecting to Appium at %s ...", self.settings.appium.appium_url)
        for attempt in range(self.settings.input.max_retries):
            try:
                self.driver = webdriver.Remote(
                    self.settings.appium.appium_url,
                    desired_caps
                )
                logger.info("Connected to iPhone successfully")
                return self.driver
            except Exception as e:
                logger.warning("Connection attempt %d failed: %s", attempt + 1, e)
                if attempt < self.settings.input.max_retries - 1:
                    time.sleep(self.settings.input.retry_delay)
                else:
                    raise RuntimeError(
                        f"Failed to connect after {self.settings.input.max_retries} attempts"
                    ) from e

    async def disconnect(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Disconnected from device")
            except Exception as e:
                logger.error("Error disconnecting: %s", e)

    def is_connected(self) -> bool:
        try:
            if self.driver:
                self.driver.current_url
                return True
        except Exception:
            pass
        return False

    async def reconnect(self) -> WebDriver:
        logger.info("Attempting reconnect...")
        await self.disconnect()
        return await self.connect()
