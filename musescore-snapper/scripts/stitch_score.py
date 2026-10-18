#!/usr/bin/env python
"""Assemble visible screenshot strips into numbered PNG score pages.

The manifest describes DOM rectangles in CSS viewport pixels, never image URLs.
Only explicitly verified blank top/bottom margins may be synthesized. Incomplete
coverage fails before publication; an existing score folder is never overwritten.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

from PIL import Image, ImageStat


class CaptureError(ValueError):
    """A capture cannot produce complete, consistently sized score pages."""


@dataclass
class Strip:
    start: int
    end: int
    pixels: Image.Image
    page_size: tuple[int, int]


def rectangle(value: dict, label: str) -> tuple[float, float, float, float]:
    try:
        numbers = tuple(float(value[key]) for key in ("x", "y", "width", "height"))
    except (KeyError, TypeError, ValueError) as exc:
        raise CaptureError(f"{label}: expected x, y, width and height.") from exc
    if not all(math.isfinite(n) for n in numbers) or min(numbers[2:]) <= 0:
        raise CaptureError(f"{label}: coordinates must be finite; sizes must be positive.")
    return numbers


def positive_int(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise CaptureError(f"{label}: expected a positive integer.")
    return value


def folder_name(title: object) -> str:
    if not isinstance(title, str):
        raise CaptureError("title: expected the confirmed song/folder name.")
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", title).strip(" .")
    if not name:
        raise CaptureError("title: no usable folder name remains.")
    return name


def extract_strip(image: Image.Image, viewport: dict, safe: dict, paper: dict) -> Strip | None:
    """Normalize one fully visible paper-width slice to screenshot pixel space."""
    try:
        vw, vh = float(viewport["width"]), float(viewport["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CaptureError("viewport: expected positive width and height.") from exc
    if not all(math.isfinite(v) and v > 0 for v in (vw, vh)):
        raise CaptureError("viewport: expected positive finite width and height.")
    scale_x, scale_y = image.width / vw, image.height / vh
    if not math.isclose(scale_x, scale_y, rel_tol=0.005):
        raise CaptureError("Screenshot/viewport aspect ratios differ; use matching browser coordinates.")
    sx, sy, sw, sh = rectangle(safe, "safe_rect")
    if sx < 0 or sy < 0 or sx + sw > vw + 0.01 or sy + sh > vh + 0.01:
        raise CaptureError("safe_rect extends outside the screenshot viewport.")
    px, py, pw, ph = rectangle(paper, "paper_rect")
    left, right = math.ceil(px * scale_x), math.floor((px + pw) * scale_x)
    top, height = py * scale_y, round(ph * scale_y)
    if left < math.ceil(sx * scale_x) or right > math.floor((sx + sw) * scale_x):
        raise CaptureError("Paper width is cropped/obscured; recapture with both sides visible.")
    # The blank-page check needs an interior after removing a one-pixel border.
    if right - left < 3 or height < 3:
        raise CaptureError(
            f"paper_rect yields {right - left}×{height} pixels; at least 3×3 are required. "
            "Re-identify the paper bounds or recapture the page."
        )
    start = max(0, math.ceil(sy * scale_y - top))
    end = min(height, math.floor((sy + sh) * scale_y - top))
    if end <= start:
        return None
    source_top = math.floor(top + start + 0.5)
    pixels = image.crop((left, source_top, right, source_top + end - start))
    return Strip(start, end, pixels, (right - left, height))


def load_strips(manifest: dict, base: Path, count: int) -> dict[int, list[Strip]]:
    groups: dict[int, list[Strip]] = {n: [] for n in range(1, count + 1)}
    captures = manifest.get("captures")
    if not isinstance(captures, list) or not captures:
        raise CaptureError("captures: provide at least one browser screenshot.")
    for index, capture in enumerate(captures, 1):
        try:
            image_path = base / capture["image"]
            pages = capture["pages"]
            if not isinstance(pages, list):
                raise CaptureError("pages: expected a list of loaded page rectangles.")
            with Image.open(image_path) as source:
                image = source.convert("RGB")
            seen = set()
            for page in pages:
                number = positive_int(page["number"], "page number")
                if number not in groups or number in seen:
                    raise CaptureError(f"Unexpected/repeated page number {number}; expected 1–{count}.")
                seen.add(number)
                strip = extract_strip(image, capture["viewport"], capture["safe_rect"], page["paper_rect"])
                if strip:
                    groups[number].append(strip)
        except (KeyError, TypeError, OSError, ValueError) as exc:
            raise CaptureError(f"Capture {index}: {exc}") from exc
    return groups


def blank_edges(value: dict, height: int, page: int) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) - {"top", "bottom"}:
        raise CaptureError(f"Page {page}: blank_edges accepts only top and bottom pixel counts.")
    top, bottom = value.get("top", 0), value.get("bottom", 0)
    if any(type(v) is not int or v < 0 for v in (top, bottom)) or top + bottom >= height:
        raise CaptureError(f"Page {page}: invalid verified blank margins.")
    return top, bottom


def choose_seam(previous: Strip, following: Strip, minimum: int) -> int:
    """Prefer a blank five-row band in the overlap, then its center."""
    low = max(previous.start, following.start, minimum)
    high = min(previous.end, following.end)
    if high - low < 5:
        return low
    center = (low + high) // 2

    def score(row: int) -> tuple[float, int]:
        brightness = []
        for strip in (previous, following):
            y = row - strip.start
            band = strip.pixels.crop((0, y - 2, strip.pixels.width, y + 3)).convert("L")
            brightness.append(ImageStat.Stat(band).mean[0])
        return min(brightness), -abs(row - center)

    return max(range(low + 2, high - 2), key=score)


def assemble_page(strips: list[Strip], margins: dict, number: int) -> Image.Image:
    if not strips:
        raise CaptureError(f"Page {number} is missing; scroll to it, confirm loading, and recapture.")
    size = strips[0].page_size
    if any(strip.page_size != size for strip in strips):
        raise CaptureError(f"Page {number}: paper size changed; keep zoom and window size fixed and recapture.")
    width, height = size
    top, bottom = blank_edges(margins, height, number)
    cursor, limit = top, height - bottom
    chain = []
    while cursor < limit:
        candidates = [s for s in strips if s.start <= cursor < s.end]
        if not candidates:
            raise CaptureError(f"Page {number}: uncovered rows starting at {cursor}/{height}; add an overlapping screenshot.")
        selected = max(candidates, key=lambda s: s.end)
        chain.append(selected)
        cursor = selected.end
    cuts = [top]
    for previous, following in zip(chain, chain[1:]):
        cuts.append(choose_seam(previous, following, cuts[-1]))
    cuts.append(limit)
    result = Image.new("RGB", size, "white")
    for strip, start, end in zip(chain, cuts, cuts[1:]):
        result.paste(strip.pixels.crop((0, start - strip.start, width, end - strip.start)), (0, start))
    # Exclude a thin border so viewer edges cannot make an unloaded white page pass.
    inset = max(1, min(width, height) // 100)
    interior = result.crop((inset, inset, width - inset, height - inset)).convert("L")
    if interior.getextrema()[0] > 200:
        raise CaptureError(f"Page {number} appears blank; verify it loaded before taking new screenshots.")
    return result


def export_score(manifest_path: Path, output_dir: Path) -> dict:
    """Publish one complete score folder, refusing existing destinations or gaps."""
    manifest_path = manifest_path.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise CaptureError("Manifest must be a JSON object.")
    title = folder_name(manifest.get("title"))
    count = positive_int(manifest.get("page_count"), "page_count")
    margins = manifest.get("blank_edges", {})
    if not isinstance(margins, dict) or set(margins) - {str(n) for n in range(1, count + 1)}:
        raise CaptureError("blank_edges keys must be expected page numbers as strings.")
    output_dir = output_dir.expanduser().resolve()
    destination = output_dir / title
    if destination.exists() or destination.is_symlink():
        raise CaptureError(f"Destination already exists: {destination}. Confirm another parent folder or title suffix.")
    strips = load_strips(manifest, manifest_path.parent, count)
    pages, hashes = [], set()
    for number in range(1, count + 1):
        image = assemble_page(strips[number], margins.get(str(number), {}), number)
        digest = hashlib.sha256(image.tobytes()).digest()
        if digest in hashes:
            raise CaptureError(f"Page {number} duplicates an earlier page; verify page numbers and recapture.")
        hashes.add(digest)
        pages.append(image)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    with tempfile.TemporaryDirectory(prefix=".musescore-", dir=output_dir) as temporary:
        staging = Path(temporary) / title
        staging.mkdir()
        for number, image in enumerate(pages, 1):
            filename = f"{number}.png"
            file = staging / filename
            image.save(file, format="PNG", optimize=True)
            summary.append({"file": str(destination / filename), "width": image.width,
                            "height": image.height, "bytes": file.stat().st_size})
        if destination.exists() or destination.is_symlink():
            raise CaptureError(f"Destination appeared during export: {destination}. No files replaced.")
        staging.rename(destination)
    return {"directory": str(destination), "page_count": count, "pages": summary}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON capture manifest; image paths are relative to it")
    parser.add_argument("--output-dir", type=Path, required=True, help="User-confirmed parent directory")
    args = parser.parse_args()
    try:
        summary = export_score(args.manifest, args.output_dir)
    except (CaptureError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
