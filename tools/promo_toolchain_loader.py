"""Resolve the external :mod:`xar_promo` package used by project builders.

The reusable promo toolchain lives in its own repository now.  Builders use the
released wheel by default (installed into the active interpreter); setting
``XAR_PROMO_SOURCE`` is an explicit, source-checkout override for local
development and acceptance work (``XAR_PROMO_TOOLCHAIN_SOURCE`` is accepted as
a compatibility alias).  The override may point at either the checkout root
or its ``src`` directory.

This module deliberately does not install packages or perform network access.
CI and callers own dependency installation, while this resolver keeps the
failure message actionable when an interpreter has not been prepared.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


PROMO_TOOLCHAIN_REPOSITORY = "https://github.com/XenoAmess/xar_promo_toolchain"
PROMO_TOOLCHAIN_VERSION = "0.2.1"
PROMO_TOOLCHAIN_RELEASE_TAG = f"v{PROMO_TOOLCHAIN_VERSION}"
PROMO_TOOLCHAIN_WHEEL_URL = (
    f"{PROMO_TOOLCHAIN_REPOSITORY}/releases/download/"
    f"{PROMO_TOOLCHAIN_RELEASE_TAG}/"
    f"xar_promo_toolchain-{PROMO_TOOLCHAIN_VERSION}-py3-none-any.whl"
)


def _source_directory(raw_value: str) -> Path:
    """Return the import root represented by ``XAR_PROMO_SOURCE``.

    Both ``.../xar_promo_toolchain`` and ``.../xar_promo_toolchain/src`` are
    accepted so a checkout and a directly prepared source path behave alike.
    """

    requested = Path(raw_value).expanduser()
    try:
        requested = requested.resolve(strict=True)
    except OSError as exc:
        raise ImportError(
            "XAR_PROMO_SOURCE does not point to an existing promo-toolchain "
            f"directory: {raw_value!r}"
        ) from exc

    candidates = (requested, requested / "src")
    for candidate in candidates:
        if (candidate / "xar_promo").is_dir():
            return candidate

    raise ImportError(
        "XAR_PROMO_SOURCE must point to the xar_promo_toolchain checkout or "
        f"its src directory; got {requested}"
    )


def ensure_promo_toolchain() -> Path | None:
    """Make the external ``xar_promo`` package importable and return its root.

    An explicit ``XAR_PROMO_SOURCE`` (or its longer compatibility alias
    ``XAR_PROMO_TOOLCHAIN_SOURCE``) always wins over an installed package. If
    no override is supplied, the active interpreter must already contain the
    released package.  ``None`` means the installed package was selected.
    """

    raw_source = os.environ.get("XAR_PROMO_SOURCE", "").strip()
    if not raw_source:
        raw_source = os.environ.get("XAR_PROMO_TOOLCHAIN_SOURCE", "").strip()
    if raw_source:
        source = _source_directory(raw_source)
        source_text = str(source)
        if source_text not in sys.path:
            sys.path.insert(0, source_text)
        return source

    if importlib.util.find_spec("xar_promo") is not None:
        return None

    raise ImportError(
        "xar_promo is not installed. Install the pinned GitHub release wheel "
        f"({PROMO_TOOLCHAIN_WHEEL_URL}) or set XAR_PROMO_SOURCE to a "
        "xar_promo_toolchain checkout (or its src directory)."
    )


__all__ = [
    "PROMO_TOOLCHAIN_RELEASE_TAG",
    "PROMO_TOOLCHAIN_REPOSITORY",
    "PROMO_TOOLCHAIN_VERSION",
    "PROMO_TOOLCHAIN_WHEEL_URL",
    "ensure_promo_toolchain",
]
