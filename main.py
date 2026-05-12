import asyncio
from typing import List, Optional

from config.settings import Settings
from core.board_detector import BoardDetector
from core.device_manager import DeviceManager
from core.input_automator import InputAutomator
from core.ocr_pipeline import OcrPipeline
from core.screen_capture import ScreenCapture
from core.solver import WordFinder
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WordleAutomation:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.device_manager = DeviceManager(self.settings)
        self.driver = None
        self.screen = None
        self.board_detector = BoardDetector(self.settings)
        self.ocr = OcrPipeline(self.settings)
        self.word_finder = WordFinder(self.settings)
        self.input_automator = None

    async def initialize(self) -> None:
        logger.info("=" * 50)
        logger.info("Wordle Automation System - Initializing")
        logger.info("=" * 50)

        self.word_finder.load_dictionary()
        self.driver = await self.device_manager.connect()
        self.screen = ScreenCapture(self.driver, self.settings)
        self.input_automator = InputAutomator(self.driver, self.settings)
        logger.info("Initialization complete")

    async def read_grid(self) -> Optional[List[List[str]]]:
        for attempt in range(3):
            screenshot = await self.screen.capture()
            self.screen.save_debug(screenshot, "board_capture")

            centers = self.board_detector.get_manual_centers()
            bbox_grid = self.board_detector.centers_to_bbox(centers)
            tile_imgs = []
            for row in bbox_grid:
                row_tiles = []
                for coords in row:
                    tile_img = self.board_detector.extract_tile(screenshot, coords)
                    row_tiles.append(tile_img)
                tile_imgs.append(row_tiles)

            letters = self.ocr.extract_grid(tile_imgs)

            flat = [ch for row in letters for ch in row]
            non_empty = sum(1 for ch in flat if ch and ch.strip())

            if non_empty >= 12:
                if self.settings.debug:
                    for r_idx, row in enumerate(letters):
                        row_str = " ".join(l or "?" for l in row)
                        logger.debug("Row %d: %s", r_idx, row_str)
                return letters

            logger.info("Grid has only %d/16 tiles read, retrying...", non_empty)
            await asyncio.sleep(0.5)

        logger.warning("Could not read full grid after 3 attempts")
        return None

    async def run_game(self) -> bool:
        await self.initialize()

        try:
            logger.info("Reading initial board...")
            await asyncio.sleep(1)
            grid = await self.read_grid()
            if grid is None:
                logger.error("Failed to read initial grid")
                return False

            total_found = 0
            consecutive_empty = 0
            round_num = 0

            while round_num < self.settings.boggle.max_attempts:
                round_num += 1
                logger.info("--- Round %d ---", round_num)

                clean = [[c or "?" for c in row] for row in grid]

                words = self.word_finder.find_words(clean)
                if not words:
                    logger.info("No valid words found on this grid")
                    break

                word, path = words[0]
                logger.info("Swiping: %s (%d letters) path: %s", word, len(word), path)
                await self.input_automator.swipe_path_indices(path)
                total_found += 1

                await asyncio.sleep(self.settings.input.after_swipe_delay)

                new_grid = await self.read_grid()
                if new_grid is None:
                    logger.warning("Could not read grid, waiting longer...")
                    await asyncio.sleep(1)
                    new_grid = await self.read_grid()
                    if new_grid is None:
                        logger.error("Grid read failed twice, stopping")
                        break

                if new_grid == grid:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        logger.info("Grid unchanged for 2 rounds, stopping")
                        break
                else:
                    consecutive_empty = 0

                grid = new_grid

            logger.info("Total words swiped: %d", total_found)
            return total_found > 0

        except Exception as e:
            logger.exception("Game loop error: %s", e)
            return False
        finally:
            await self.device_manager.disconnect()

    async def run_multiple(self, count: int = 1) -> None:
        successes = 0
        for i in range(count):
            logger.info("\n=== Game %d/%d ===", i + 1, count)
            try:
                result = await self.run_game()
                if result:
                    successes += 1
                if i < count - 1:
                    logger.info("Waiting before next game...")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error("Game %d failed: %s", i + 1, e)
        logger.info("Results: %d/%d completed", successes, count)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="iPhone Wordle Automation System")
    parser.add_argument("--games", type=int, default=1, help="Number of games to play")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--bundle-id", type=str, default=None, help="iOS app bundle ID (default: com.triumphsdkprod)")
    args = parser.parse_args()

    settings = Settings()
    if args.debug:
        settings.debug = True
    if args.bundle_id:
        settings.appium.bundle_id = args.bundle_id

    automation = WordleAutomation(settings)
    await automation.run_multiple(args.games)


if __name__ == "__main__":
    asyncio.run(main())
