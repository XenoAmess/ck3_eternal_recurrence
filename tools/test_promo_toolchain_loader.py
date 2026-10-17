#!/usr/bin/env python3
"""Contract tests for the parent repository's external promo-toolchain pin."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS_DIRECTORY = Path(__file__).resolve().parent
if str(TOOLS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIRECTORY))

import promo_toolchain_loader as loader  # noqa: E402


EXPECTED_VERSION = "0.3.0"
EXPECTED_SHA256 = (
    "f59c4b62b89297e2ff7bb7df4354fc88c6447fa6b1b7eade28de2bc1e6dc974c"
)


class PromoToolchainPinTests(unittest.TestCase):
    def test_loader_and_hashed_requirement_select_the_same_release_wheel(self) -> None:
        expected_url = (
            "https://github.com/XenoAmess/xar_promo_toolchain/releases/download/"
            f"v{EXPECTED_VERSION}/"
            f"xar_promo_toolchain-{EXPECTED_VERSION}-py3-none-any.whl"
        )
        requirement = (
            TOOLS_DIRECTORY / "requirements-promo-toolchain.txt"
        ).read_text(encoding="utf-8")

        self.assertEqual(loader.PROMO_TOOLCHAIN_VERSION, EXPECTED_VERSION)
        self.assertEqual(loader.PROMO_TOOLCHAIN_RELEASE_TAG, f"v{EXPECTED_VERSION}")
        self.assertEqual(loader.PROMO_TOOLCHAIN_WHEEL_URL, expected_url)
        self.assertIn(expected_url, requirement)
        self.assertIn(f"--hash=sha256:{EXPECTED_SHA256}", requirement)


if __name__ == "__main__":
    unittest.main()
