from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .base import ImageProvider
from .codex_oauth import CodexOAuthImageProvider, codex_auth_file as default_codex_auth_file
from .openai_provider import OpenAIImageProvider

DEFAULT_BACKEND = "auto"
VALID_BACKENDS = {"auto", "codex-oauth", "openai"}


def create_image_provider(
    *,
    api_key: Optional[str],
    base_url: Optional[str],
    backend: Optional[str] = None,
    codex_auth_file: Optional[Path] = None,
) -> ImageProvider:
    selected = _normalize_backend(backend)
    if selected == "auto":
        if CodexOAuthImageProvider.available(codex_auth_file):
            return CodexOAuthImageProvider(auth_file=codex_auth_file)
        return OpenAIImageProvider(api_key=api_key, base_url=base_url)
    if selected == "codex-oauth":
        if not CodexOAuthImageProvider.available(codex_auth_file):
            expected = codex_auth_file or default_codex_auth_file()
            raise RuntimeError(f"Codex OAuth auth is missing. Expected {expected}.")
        return CodexOAuthImageProvider(auth_file=codex_auth_file)
    if selected == "openai":
        return OpenAIImageProvider(api_key=api_key, base_url=base_url)
    raise ValueError(f"Unsupported image backend: {selected}")


def _normalize_backend(backend: Optional[str]) -> str:
    selected = (
        backend
        or os.getenv("IMAGE_GENERATOR_IMAGE_BACKEND")
        or os.getenv("IMAGE2_IMAGE_BACKEND")
        or os.getenv("CODEX_PPT_IMAGE_BACKEND")
        or DEFAULT_BACKEND
    ).strip().lower()
    if selected not in VALID_BACKENDS:
        raise ValueError(
            f"Unsupported image backend: {selected}. Expected one of: {', '.join(sorted(VALID_BACKENDS))}."
        )
    return selected
