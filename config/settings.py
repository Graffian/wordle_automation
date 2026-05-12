from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AppiumSettings:
    platform_name: str = "iOS"
    platform_version: str = "17.4"
    device_name: str = "iPhone 15"
    automation_name: str = "XCUITest"
    wda_port: int = 8100
    appium_host: str = "http://127.0.0.1"
    appium_port: int = 4723
    bundle_id: str = "com.triumphsdkprod"
    use_prebuilt_wda: bool = False
    wda_bundle_id: str = "com.facebook.WebDriverAgentRunner.xctrunner"
    no_reset: bool = True
    full_reset: bool = False

    @property
    def appium_url(self) -> str:
        return f"{self.appium_host}:{self.appium_port}"


@dataclass
class BoardSettings:
    rows: int = 4
    cols: int = 4
    grid_top_ratio: float = 0.25
    grid_left_ratio: float = 0.10
    grid_width_ratio: float = 0.80
    tile_aspect_min: float = 0.6
    tile_aspect_max: float = 1.4
    tile_area_min: int = 500
    tile_area_max: int = 40000
    min_tiles_for_auto: int = 12
    canny_low: int = 50
    canny_high: int = 150
    tile_centers: list = field(default_factory=lambda: [
        [(254, 1151), (511, 1166), (790, 1160), (1037, 1151)],
        [(235, 1420), (514, 1417), (762, 1401), (1072, 1429)],
        [(244, 1693), (508, 1686), (787, 1686), (1059, 1664)],
        [(244, 1956), (520, 1950), (771, 1925), (1075, 1962)],
    ])


@dataclass
class ScreenSettings:
    width: int = 1320
    height: int = 2868
    capture_format: str = "png"
    screenshot_cache_ttl: float = 0.3


@dataclass
class BoggleSettings:
    min_word_length: int = 3
    max_word_length: int = 16
    use_8_directions: bool = True
    score_target: int = 100
    max_attempts: int = 20


@dataclass
class ColorSettings:
    white_lower: tuple = (0, 0, 180)
    white_upper: tuple = (180, 50, 255)
    tile_bg_lower: tuple = (0, 0, 100)
    tile_bg_upper: tuple = (180, 60, 200)


@dataclass
class InputSettings:
    swipe_segment_delay: float = 0.01
    swipe_press_duration: float = 0.05
    after_swipe_delay: float = 1.5
    retry_delay: float = 2.0
    max_retries: int = 3


@dataclass
class Settings:
    appium: AppiumSettings = field(default_factory=AppiumSettings)
    board: BoardSettings = field(default_factory=BoardSettings)
    screen: ScreenSettings = field(default_factory=ScreenSettings)
    boggle: BoggleSettings = field(default_factory=BoggleSettings)
    colors: ColorSettings = field(default_factory=ColorSettings)
    input: InputSettings = field(default_factory=InputSettings)
    debug: bool = False
    log_level: str = "INFO"
    screenshot_dir: str = "screenshots"
