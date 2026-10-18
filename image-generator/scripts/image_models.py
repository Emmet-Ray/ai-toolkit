"""Model defaults and capabilities shared by the image CLI and its runtime.

Match exact model IDs and dated snapshots so a GPT Image 2 rule cannot
accidentally apply to GPT Image 2.5. Provider namespaces are supported.
"""

from dataclasses import dataclass
import re
from typing import FrozenSet


DEFAULT_MODEL = "gpt-image-2.5-sunburst"
BASE_QUALITIES = frozenset({"low", "medium", "high", "auto"})


@dataclass(frozen=True)
class ImageModelCapabilities:
    flexible_sizes: bool
    qualities: FrozenSet[str]
    input_fidelity: bool


LEGACY = ImageModelCapabilities(False, BASE_QUALITIES, True)
IMAGE_2 = ImageModelCapabilities(True, BASE_QUALITIES, False)
IMAGE_25 = ImageModelCapabilities(True, BASE_QUALITIES | {"xhigh", "max"}, False)


def model_capabilities(model: str) -> ImageModelCapabilities:
    """Return the option contract for a model, retaining legacy proxy behavior."""
    name = model.rsplit("/", 1)[-1]
    if re.fullmatch(r"gpt-image-2\.5-(sunburst|flare)(-\d{4}-\d{2}-\d{2})?", name):
        return IMAGE_25
    if re.fullmatch(r"gpt-image-2(-\d{4}-\d{2}-\d{2})?", name):
        return IMAGE_2
    return LEGACY
