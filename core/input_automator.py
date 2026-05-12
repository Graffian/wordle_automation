import asyncio
from typing import List, Tuple

from utils.logger import setup_logger
from config.settings import Settings

logger = setup_logger(__name__)


class InputAutomator:
    def __init__(self, device_mgr, settings: Settings):
        self._device = device_mgr
        self.settings = settings

    async def swipe_word(self, tile_centers: List[Tuple[int, int]]) -> None:
        if not tile_centers:
            return

        actions = {
            "actions": [{
                "type": "pointer",
                "id": "finger1",
                "parameters": {"pointerType": "touch"},
                "actions": [
                    {
                        "type": "pointerMove",
                        "duration": 0,
                        "x": tile_centers[0][0],
                        "y": tile_centers[0][1],
                    },
                    {"type": "pointerDown", "button": 0},
                ]
            }]
        }

        for x, y in tile_centers[1:]:
            actions["actions"][0]["actions"].append({
                "type": "pointerMove",
                "duration": 50,
                "x": x,
                "y": y,
            })

        actions["actions"][0]["actions"].append(
            {"type": "pointerUp", "button": 0}
        )

        await self._device.perform_actions(actions)
        await asyncio.sleep(self.settings.input.after_swipe_delay)

    async def swipe_path_indices(
        self, path: List[Tuple[int, int]]
    ) -> None:
        centers = self.settings.board.tile_centers
        coords = [centers[r][c] for r, c in path]
        await self.swipe_word(coords)
