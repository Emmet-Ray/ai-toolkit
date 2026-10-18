"""Image model compatibility checks; all CLI requests are dry runs."""

import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import image_gen
from image_models import DEFAULT_MODEL, model_capabilities
import runtime


class ImageModelTests(unittest.TestCase):
    def test_cli_and_runtime_share_default_but_preserve_overrides(self):
        self.assertEqual(DEFAULT_MODEL, "gpt-image-2.5-sunburst")
        self.assertEqual(image_gen.DEFAULT_MODEL, runtime.DEFAULT_MODEL)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(image_gen._default_model(), DEFAULT_MODEL)
            for key in ("IMAGE_GENERATOR_IMAGE_MODEL", "IMAGE2_IMAGE_MODEL", "CODEX_PPT_IMAGE_MODEL"):
                with self.subTest(key=key), patch.dict(os.environ, {key: "gpt-image-2"}):
                    self.assertEqual(image_gen._default_model(), "gpt-image-2")

    def test_25_variants_snapshots_and_provider_namespaces(self):
        for model in ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare",
                      "gpt-image-2.5-sunburst-2026-09-08", "openai/gpt-image-2.5-flare-2026-09-08"):
            with self.subTest(model=model):
                spec = model_capabilities(model)
                self.assertTrue(spec.flexible_sizes)
                self.assertIn("max", spec.qualities)
                self.assertIn("xhigh", spec.qualities)
                self.assertFalse(spec.input_fidelity)

    def test_older_models_do_not_inherit_25_quality_settings(self):
        for model in ("gpt-image-2", "openai/gpt-image-2-2026-04-21", "gpt-image-1.5"):
            with self.subTest(model=model):
                self.assertNotIn("max", model_capabilities(model).qualities)
                self.assertNotIn("xhigh", model_capabilities(model).qualities)


class ImageModelCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cli = Path(__file__).with_name("image_gen.py")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith((
            "IMAGE_GENERATOR_", "IMAGE2_", "CODEX_PPT_", "OPENAI_",
        ))}
        self.env.update(IMAGE_GENERATOR_HOME=str(self.root / "runtime"), PYTHONDONTWRITEBYTECODE="1")

    def run_cli(self, command="generate", *options):
        arguments = [sys.executable, str(self.cli), command, "--backend", "openai", "--dry-run"]
        if command != "generate-batch":
            arguments += ["--prompt", "A blue printing press", "--out", str(self.root / "image.png")]
        return subprocess.run(arguments + list(options), env=self.env, text=True, capture_output=True)

    def test_default_generates_flexible_size_png_request(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["model"], DEFAULT_MODEL)
        self.assertEqual(payload["size"], "2048x1152")
        self.assertEqual(payload["quality"], "medium")

    def test_transparent_background_and_extended_quality_for_25(self):
        for model in ("gpt-image-2.5-sunburst", "gpt-image-2.5-flare-2026-09-08"):
            with self.subTest(model=model):
                result = self.run_cli("generate", "--model", model, "--background", "transparent",
                                      "--quality", "max", "--size", "2048x2048")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["background"], "transparent")
                self.assertEqual(payload["quality"], "max")

    def test_image_2_transparency_preview_retains_older_quality_limits(self):
        result = self.run_cli("generate", "--model", "gpt-image-2", "--background", "transparent")
        self.assertEqual(result.returncode, 0, result.stderr)
        for quality in ("xhigh", "max"):
            result = self.run_cli("generate", "--model", "gpt-image-2", "--quality", quality)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("quality for gpt-image-2", result.stderr)

    def test_legacy_model_keeps_fixed_sizes_and_fidelity(self):
        image = self.root / "input.png"
        image.write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="
        ))
        result = self.run_cli("edit", "--model", "gpt-image-1.5", "--size", "1024x1024",
                              "--image", str(image), "--input-fidelity", "high")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["input_fidelity"], "high")
        result = self.run_cli("generate", "--model", "gpt-image-1.5", "--size", "2048x1152")
        self.assertNotEqual(result.returncode, 0)

    def test_modern_models_reject_legacy_fidelity_before_request(self):
        for model in ("gpt-image-2", "gpt-image-2.5-sunburst"):
            result = self.run_cli("edit", "--model", model, "--image", "missing.png", "--input-fidelity", "high")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("omit it", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_batch_checks_each_jobs_model_and_quality(self):
        jobs = self.root / "jobs.jsonl"
        jobs.write_text(json.dumps({"prompt": "A blue press", "model": "gpt-image-2.5-flare", "quality": "xhigh"}))
        result = self.run_cli("generate-batch", "--input", str(jobs), "--out-dir", str(self.root / "batch"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"quality": "xhigh"', result.stdout)
        jobs.write_text(json.dumps({"prompt": "A blue press", "model": "gpt-image-2", "quality": "max"}))
        result = self.run_cli("generate-batch", "--input", str(jobs), "--out-dir", str(self.root / "batch"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("quality for gpt-image-2", result.stderr)

    def test_runtime_pin_overrides_new_default(self):
        folder = self.root / "runtime"
        folder.mkdir()
        (folder / ".env").write_text("IMAGE_GENERATOR_IMAGE_MODEL=gpt-image-2\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["model"], "gpt-image-2")
        result = self.run_cli("generate", "--model", "gpt-image-2.5-flare")
        self.assertEqual(json.loads(result.stdout)["model"], "gpt-image-2.5-flare")


if __name__ == "__main__":
    unittest.main()
