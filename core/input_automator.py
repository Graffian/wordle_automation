import asyncio
from typing import List, Tuple

from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class InputAutomator:
    def __init__(self, driver: WebDriver, settings: Settings):
        self.driver = driver
        self.settings = settings

    async def swipe_word(self, tile_centers: List[Tuple[int, int]]) -> None:
        if not tile_centers:
            return

        finger = PointerInput(interaction.POINTER_TOUCH, "finger")
        action = ActionBuilder(self.driver, mouse=finger)

        first_x, first_y = tile_centers[0]
        action.pointer_action.move_to_location(first_x, first_y)
        action.pointer_action.pointer_down()

        for x, y in tile_centers[1:]:
            action.pointer_action.move_to_location(x, y)
            action.pointer_action.pause(self.settings.input.swipe_segment_delay)

        action.pointer_action.pause(self.settings.input.swipe_press_duration)
        action.pointer_action.release()
        action.perform()

        await asyncio.sleep(self.settings.input.after_swipe_delay)

    async def swipe_path_indices(
        self, path: List[Tuple[int, int]]
    ) -> None:
        centers = self.settings.board.tile_centers
        coords = [centers[r][c] for r, c in path]
        await self.swipe_word(coords)
