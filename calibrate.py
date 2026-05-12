"""
Calibration tool for Boggle Automation.
 
Given a screenshot of the game screen, this tool analyzes the layout
and prints recommended settings for config/settings.py.

Usage:
    python calibrate.py path/to/screenshot.png
"""

import sys
import cv2
import numpy as np


def analyze_screenshot(path: str):
    img = cv2.imread(path)
    if img is None:
        print(f"Error: Could not load {path}")
        return

    h, w = img.shape[:2]
    print(f"Screen resolution: {w}x{h}")
    print(f"Update screen.width = {w}, screen.height = {h} in settings.py")
    print()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Find all tile-like squares via adaptive threshold + contours
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    tiles = []
    for cnt in contours:
        x, y, tw, th = cv2.boundingRect(cnt)
        area = tw * th
        if 0.7 < tw / th < 1.3 and 500 < area < 50000 and y > 200:
            tiles.append((x, y, tw, th))

    # Group into rows
    if not tiles:
        print("No tiles found via edge detection — trying color-based detection...")
        # Try finding gray tiles
        gray_mask = cv2.inRange(img, np.array([150, 150, 150]), np.array([220, 220, 220]))
        gray_contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in gray_contours:
            x, y, tw, th = cv2.boundingRect(cnt)
            area = tw * th
            if 0.7 < tw / th < 1.3 and 200 < area < 30000 and y > 200:
                tiles.append((x, y, tw, th))

    if not tiles:
        print("Still no tiles found. Try a different screenshot with better contrast.")
        return

    tiles.sort(key=lambda t: (t[1], t[0]))

    # Group by row
    rows = {}
    for t in tiles:
        x, y, tw, th = t
        row_key = round(y / 260)
        rows.setdefault(row_key, []).append(t)

    print(f"Found {len(tiles)} tile-like objects in {len(rows)} row groups")
    print()

    # Display each row
    col_candidates = []
    for rk in sorted(rows.keys()):
        row_tiles = rows[rk]
        row_tiles.sort(key=lambda t: t[0])
        centers = [(t[0] + t[2] // 2, t[1] + t[3] // 2) for t in row_tiles]
        avg_y = int(np.mean([c[1] for c in centers]))
        col_centers = [c[0] for c in centers]

        if len(col_centers) >= 3:
            col_candidates.append(col_centers)
            x_str = ", ".join(f"x={c:4d} ({c/w:.3f})" for c in col_centers)
            print(
                f"  Row at y={avg_y:4d} ({avg_y/h:.3f}): {len(row_tiles)} cols — {x_str}"
            )

    print()

    # Determine the most common number of columns
    if col_candidates:
        col_counts = {}
        for cols in col_candidates:
            n = len(cols)
            col_counts[n] = col_counts.get(n, 0) + 1

        best_n = max(col_counts, key=col_counts.get)
        print(
            f"Most common column count: {best_n} "
            f"(appeared in {col_counts[best_n]}/{len(col_candidates)} rows)"
        )

        # Average column positions across all rows with this count
        matching = [c for c in col_candidates if len(c) == best_n]
        if matching:
            avg_cols = np.mean(matching, axis=0).astype(int)
            print()
            print("Recommended column x-centers:")
            for i, cx in enumerate(avg_cols):
                print(f"  Col {i}: x={cx} ({cx/w:.3f})")

    # Detect letter bank region (lower portion with content)
    print()
    print("=== Letter Bank / Lower Region ===")
    lower = img[int(h * 0.55):, :]
    lh, lw = lower.shape[:2]
    lgray = cv2.cvtColor(lower, cv2.COLOR_BGR2GRAY)
    _, lt = cv2.threshold(lgray, 200, 255, cv2.THRESH_BINARY_INV)
    l_contours, _ = cv2.findContours(lt, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    y_offset = int(h * 0.55)
    buttons = []
    for cnt in l_contours:
        x, y, tw, th = cv2.boundingRect(cnt)
        area = tw * th
        abs_y = y + y_offset
        if 0.3 < tw / th < 3.0 and 100 < area < 50000 and abs_y > 1500:
            buttons.append((x, abs_y, tw, th, area))

    buttons.sort(key=lambda b: (b[1], b[0]))
    print(f"Found {len(buttons)} objects in lower 45%:")
    for b in buttons:
        x, y, tw, th, area = b
        cx, cy = x + tw // 2, y + th // 2
        ratio = tw / th
        label = ""
        if 0.8 < ratio < 1.2:
            label = " (square — possible tile)"
        elif 2.0 < ratio < 5.0 and th < 50:
            label = " (thin bar — possible separator)"
        elif 2.0 < ratio < 5.0 and th > 50:
            label = " (wide — possible button)"
        print(
            f"  ({x:4d},{y:4d}) {tw}x{th} "
            f"center=({cx:4d},{cy:4d}) ratio={ratio:.2f}{label}"
        )

    print()
    print("=== Next Steps ===")
    print("1. Update screen.width and screen.height in config/settings.py")
    print("2. Update the board detection settings if columns look wrong")
    print("3. Check the detected tile positions visually")
    print("4. Use find_coords.py to click each of the 16 tile centers")
    print("5. Paste the (x,y) coordinates into board.tile_centers in config/settings.py")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calibrate.py <screenshot.png>")
        sys.exit(1)
    analyze_screenshot(sys.argv[1])
