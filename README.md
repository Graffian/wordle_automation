# iPhone Boggle Automation System

Automatically plays a Boggle-style word game inside Triumph Arcade on an iPhone via USB using computer vision, OCR, and touch automation via tidevice + WebDriverAgent.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Laptop (Brain)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │  Board    │  │   OCR    │  │  Solver  │  │ Input  ││
│  │ Detector  │──│ Pipeline │──│(WordFind)│──│Automator││
│  └────┬─────┘  └──────────┘  └──────────┘  └───┬────┘│
│       │                                         │     │
│  ┌────▼──────────────────────────────────────────▼──┐ │
│  │              Main Game Loop (main.py)             │ │
│  └────┬──────────────────────┬──────────────────────┘ │
│       │                      │                        │
│  ┌────▼──────┐         ┌─────▼────────┐               │
│  │   Screen   │         │  Device Mgr  │               │
│  │  Capture   │         │ (tidevice +  │               │
│  │            │         │  WDA HTTP)   │               │
│  └────┬──────┘         └─────┬────────┘               │
└───────┼──────────────────────┼─────────────────────────┘
        │ USB                  │ USB
  ┌─────▼──────────────────────▼──────┐
  │         iPhone                     │
  │  ┌─────────────────────────────┐  │
  │  │  Triumph Arcade + Boggle   │  │
  │  └─────────────────────────────┘  │
  │         WebDriverAgent            │
  └────────────────────────────────────┘
```

## System Requirements

- **macOS** or **Windows** or **Linux**
- Python 3.9+
- iPhone with USB cable
- Tesseract OCR
- Developer Mode enabled on iPhone
- **No Xcode or Appium required**

## Installation

### 1. System Dependencies

```bash
# macOS
brew install libimobiledevice tesseract

# Ubuntu/Debian
sudo apt update
sudo apt install libimobiledevice-dev libusbmuxd-dev tesseract-ocr
```

### 2. Python Environment

```bash
cd wordle_automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. iOS Setup

1. Connect iPhone via USB
2. Trust the computer on iPhone
3. Enable Developer Mode (Settings > Privacy & Security > Developer Mode)
4. Verify connection: `idevice_id -l`

**No Xcode or Appium needed.** The tool uses `tidevice` (Python) to start WebDriverAgent on the device using a prebuilt binary.

## Finding the Bundle ID

If the default bundle ID doesn't match your app, find it with:

```bash
# List all installed apps and their bundle IDs
ideviceinstaller -l
```

Or look up the app on App Store databases (e.g., AppBrain, Apptopia).

## Usage

```bash
# Activate environment
source venv/bin/activate

# Open Triumph Arcade on iPhone, navigate to the Boggle game, then:
python main.py

# Debug mode (saves screenshots, verbose logging)
python main.py --debug

# Play multiple games
python main.py --games 5

# Different app bundle ID
python main.py --bundle-id com.example.otherapp
```

## Project Structure

```
wordle_automation/
├── config/
│   └── settings.py        # All configurable parameters
├── core/
│   ├── device_manager.py   # Appium + WDA connection management
│   ├── screen_capture.py   # iPhone screenshot capture
│   ├── board_detector.py   # CV-based grid detection
│   ├── ocr_pipeline.py     # Tesseract OCR for letters
│   ├── color_recognizer.py # HSV-based tile color classification
│   ├── solver.py           # Boggle word finder (Trie + DFS)
│   └── input_automator.py  # W3C swipe gesture automation
├── utils/
│   └── logger.py           # Logging configuration
├── assets/                 # Debug screenshots
├── logs/                   # Automation logs
├── main.py                 # Main game loop
├── requirements.txt
└── setup.sh
```

## Configuration

Edit `config/settings.py` to tune:

| Setting | Description |
|---------|-------------|
| `screen.width/height` | iPhone resolution (default: iPhone 15: 1290x2796) |
| `board.tile_centers` | 4x4 grid of tile center (x,y) coordinates |
| `boggle.min_word_length` | Minimum word length (default: 3) |
| `boggle.max_word_length` | Maximum word length (default: 16) |
| `boggle.score_target` | Target score before stopping |
| `input.swipe_segment_delay` | Delay between swipe segments |
| `input.after_swipe_delay` | Delay after each word swipe |

## How It Works

1. **Connection** — Appium connects via USB using WebDriverAgent
2. **Capture** — Screenshot taken from iPhone screen
3. **OCR** — Tesseract extracts letters from each of the 16 tiles
4. **Solver** — Trie-based DFS finds all valid Boggle words on the grid with their tile-path indices
5. **Input** — W3C pointer actions swipe through each word's tile path (auto-submit on finger-lift)
6. **Loop** — Re-read grid and repeat until no new words can be formed

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No iOS devices detected` | Check USB cable, run `idevice_id -l`, trust computer |
| `Appium connection refused` | Ensure Appium server is running on port 4723 |
| WDA build fails | Open WebDriverAgent.xcodeproj, set signing team |
| OCR returns wrong letters | Tune `ocr_pipeline.py` preprocessing or adjust tile coordinates in `board.tile_centers` |
| Swipe misses tiles | Re-run `find_coords.py` and update `board.tile_centers` in settings.py |

## Modules

### `core/board_detector.py`
- Edge detection to find tile bounding boxes (auto-detection)
- Falls back to ratio-based grid when edge detection yields <10 tiles
- Supports manual `tile_centers` from calibration for precise swipe coordinates

### `core/ocr_pipeline.py`
- Two-pass OCR with different preprocessing (Otsu threshold + CLAHE)
- Tesseract with PSM 10 (single character) and OEM 3 (LSTM)
- Whitelist: A-Z only

### `core/input_automator.py`
- W3C pointer actions (`PointerInput` + `ActionBuilder`)
- `swipe_word()` — smooth multi-point swipe through a path of tile centers
- `swipe_path_indices()` — converts (row,col) path to screen coordinates

### `core/solver.py`
- Trie-based Boggle word finder with DFS over 4x4 grid
- Built-in ~4000+ word dictionary (3-8 letters)
- Returns `(word, [(r,c), ...])` tuples sorted by length (longest first)

## License

MIT
