"""Behavior tests with generated score-like pages; no network or real scores."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

from stitch_score import CaptureError, export_score


class ExportScoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.manifest = {"title": "测试曲谱", "page_count": 1, "captures": []}
        self.page = Image.new("RGB", (100, 200), "white")
        draw = ImageDraw.Draw(self.page)
        for y in (30, 70, 110, 160):
            for offset in range(5):
                draw.line((10, y + offset * 2, 90, y + offset * 2), fill="black")
            draw.ellipse((40, y - 3, 46, y + 3), fill="black")

    def capture(self, top, *, page_number=1, scale=1, page=None):
        page = self.page if page is None else page
        screenshot = Image.new("RGB", (160, 130), "#ccc")
        screenshot.paste(page, (20, top))
        # A dark toolbar must never be copied into a reconstructed page.
        ImageDraw.Draw(screenshot).rectangle((0, 0, 159, 19), fill="#223344")
        if scale != 1:
            screenshot = screenshot.resize((160 * scale, 130 * scale), Image.Resampling.NEAREST)
        filename = f"capture-{len(self.manifest['captures'])}.png"
        screenshot.save(self.root / filename)
        capture = {
            "image": filename,
            "viewport": {"width": 160, "height": 130},
            "safe_rect": {"x": 0, "y": 20, "width": 160, "height": 110},
            "pages": [{"number": page_number, "paper_rect": {
                "x": 20, "y": top, "width": 100, "height": 200,
            }}],
        }
        self.manifest["captures"].append(capture)
        return capture

    def export(self):
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        return export_score(manifest_path, self.output)

    def test_reconstructs_exact_pixels_and_numbered_png_at_1x_and_2x(self):
        for scale in (1, 2):
            with self.subTest(scale=scale):
                self.manifest["title"] = f"测试曲谱 {scale}"
                self.manifest["captures"] = []
                self.capture(20, scale=scale)
                self.capture(-70, scale=scale)
                result = self.export()
                folder = Path(result["directory"])
                self.assertEqual([f.name for f in folder.iterdir()], ["1.png"])
                with Image.open(folder / "1.png") as actual:
                    expected = self.page.resize((100 * scale, 200 * scale), Image.Resampling.NEAREST)
                    self.assertEqual(actual.format, "PNG")
                    self.assertEqual(actual.size, expected.size)
                    self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_missing_page_does_not_publish_partial_score(self):
        self.manifest["page_count"] = 2
        self.capture(20)
        self.capture(-70)
        with self.assertRaisesRegex(CaptureError, "Page 2 is missing"):
            self.export()
        self.assertFalse((self.output / "测试曲谱").exists())

    def test_tiny_paper_reports_actionable_cli_error_without_traceback(self):
        for width, height in ((2, 2), (1, 20), (20, 1)):
            with self.subTest(size=(width, height)):
                self.manifest["captures"] = []
                capture = self.capture(20)
                capture["pages"][0]["paper_rect"].update(width=width, height=height)
                manifest_path = self.root / "manifest.json"
                manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).with_name("stitch_score.py")),
                     str(manifest_path), "--output-dir", str(self.output)],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("Re-identify the paper bounds or recapture", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.output / "测试曲谱").exists())

    def test_half_pixel_bounds_preserve_rows_and_exclude_viewer_edges(self):
        # Fixed raster placements represent half-CSS-pixel bounds at each DPR.
        # The outer half-pixel columns at 1× contain viewer border colors.
        for scale, paper_left, first_top, second_top, page_width in (
            (1, 21, 21, -70, 99),
            (2, 41, 41, -141, 200),
        ):
            with self.subTest(scale=scale):
                self.manifest["title"] = f"小数坐标 {scale}"
                self.manifest["captures"] = []
                expected = self.page.resize((100 * scale, 200 * scale), Image.Resampling.NEAREST)
                expected = expected.crop((0, 0, page_width, 200 * scale))
                # Encode every row so a dropped/repeated row cannot hide in whitespace.
                for y in range(expected.height):
                    expected.putpixel((5, y), (y % 251, 0, 0))
                for index, (css_top, raster_top) in enumerate(((20.5, first_top), (-70.5, second_top))):
                    screenshot = Image.new("RGB", (160 * scale, 130 * scale), "#885599")
                    screenshot.paste(expected, (paper_left, raster_top))
                    ImageDraw.Draw(screenshot).rectangle(
                        (0, 0, screenshot.width - 1, 20 * scale - 1), fill="#223344",
                    )
                    filename = f"fractional-{scale}-{index}.png"
                    screenshot.save(self.root / filename)
                    self.manifest["captures"].append({
                        "image": filename,
                        "viewport": {"width": 160, "height": 130},
                        "safe_rect": {"x": 0, "y": 20, "width": 160, "height": 110},
                        "pages": [{"number": 1, "paper_rect": {
                            "x": 20.5, "y": css_top, "width": 100, "height": 200,
                        }}],
                    })
                result = self.export()
                with Image.open(result["pages"][0]["file"]) as actual:
                    self.assertEqual(actual.size, expected.size)
                    self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_gap_requires_recapture(self):
        self.capture(20)
        self.capture(-100)
        with self.assertRaisesRegex(CaptureError, "uncovered rows"):
            self.export()

    def test_existing_folder_is_preserved(self):
        self.capture(20)
        self.capture(-70)
        self.export()
        before = (self.output / "测试曲谱/1.png").read_bytes()
        with self.assertRaisesRegex(CaptureError, "Destination already exists"):
            self.export()
        self.assertEqual((self.output / "测试曲谱/1.png").read_bytes(), before)

    def test_only_explicit_blank_edge_can_fill_unseen_rows(self):
        self.capture(15)
        self.capture(-70)
        with self.assertRaisesRegex(CaptureError, "uncovered rows starting at 0"):
            self.export()
        self.manifest["blank_edges"] = {"1": {"top": 5}}
        result = self.export()
        with Image.open(result["pages"][0]["file"]) as actual:
            self.assertEqual(actual.tobytes(), self.page.tobytes())

    def test_rejects_horizontal_crop(self):
        capture = self.capture(20)
        capture["safe_rect"].update(x=30, width=130)
        with self.assertRaisesRegex(CaptureError, "Paper width is cropped"):
            self.export()

    def test_rejects_changed_zoom(self):
        self.capture(20)
        capture = self.capture(-70)
        capture["pages"][0]["paper_rect"]["height"] = 210
        with self.assertRaisesRegex(CaptureError, "paper size changed"):
            self.export()

    def test_rejects_unloaded_white_page(self):
        blank = Image.new("RGB", (100, 200), "white")
        self.capture(20, page=blank)
        self.capture(-70, page=blank)
        with self.assertRaisesRegex(CaptureError, "appears blank"):
            self.export()

    def test_rejects_duplicate_pages(self):
        self.manifest["page_count"] = 2
        for number in (1, 2):
            self.capture(20, page_number=number)
            self.capture(-70, page_number=number)
        with self.assertRaisesRegex(CaptureError, "duplicates an earlier page"):
            self.export()

    def test_multiple_pages_preserve_order_and_chinese_folder_name(self):
        self.manifest["page_count"] = 2
        second = self.page.copy()
        ImageDraw.Draw(second).rectangle((60, 180, 70, 190), fill="black")
        # Capture order need not match page order.
        for number, page in ((2, second), (1, self.page)):
            self.capture(20, page_number=number, page=page)
            self.capture(-70, page_number=number, page=page)
        result = self.export()
        self.assertEqual(Path(result["directory"]).name, "测试曲谱")
        for expected, record in zip((self.page, second), result["pages"]):
            with Image.open(record["file"]) as actual:
                self.assertEqual(actual.tobytes(), expected.tobytes())
        self.assertEqual([Path(p["file"]).name for p in result["pages"]], ["1.png", "2.png"])


if __name__ == "__main__":
    unittest.main()
