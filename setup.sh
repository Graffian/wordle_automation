#!/bin/bash
set -e

echo "========================================"
echo "  Wordle iPhone Automation - Setup"
echo "========================================"

# 1. System dependencies
echo ""
echo "[1/6] Checking system dependencies..."

# Check if running on macOS (required for Xcode)
if [[ "$(uname)" != "Darwin" ]]; then
    echo "WARNING: This setup requires macOS for iOS development tools."
    echo "Continuing anyway..."
fi

# 2. Check Python
echo ""
echo "[2/6] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERROR: Python 3 not found. Install Python 3.10+ first."
    exit 1
fi
echo "Found: $($PYTHON --version)"

# 3. Create virtual environment
echo ""
echo "[3/6] Creating virtual environment..."
$PYTHON -m venv venv
source venv/bin/activate
echo "Virtual environment activated"

# 4. Install Python dependencies
echo ""
echo "[4/6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install Tesseract
echo ""
echo "[5/6] Checking Tesseract OCR..."
if command -v tesseract &>/dev/null; then
    echo "Tesseract found: $(tesseract --version 2>&1 | head -1)"
else
    echo ""
    echo "Tesseract not found. Install with:"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu: sudo apt install tesseract-ocr"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
    echo "Then verify: tesseract --list-langs"
fi

# 6. Setup instructions
echo ""
echo "[6/6] Setup checklist"
echo ""
echo "========================================"
echo "  MANUAL SETUP REQUIRED"
echo "========================================"
echo ""
echo "1. Install Homebrew (if not installed):"
echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
echo ""
echo "2. Install libimobiledevice:"
echo "   brew install libimobiledevice"
echo ""
echo "3. Install Appium:"
echo "   npm install -g appium"
echo "   appium driver install xcuitest"
echo ""
echo "4. Install WebDriverAgent (included with Appium XCUITest driver)"
echo ""
echo "5. Start Appium server:"
echo "   appium"
echo ""
echo "6. Connect iPhone via USB and trust the computer"
echo ""
echo "7. Run the automation:"
echo "   source venv/bin/activate"
echo "   python main.py --debug"
echo ""
echo "========================================"
