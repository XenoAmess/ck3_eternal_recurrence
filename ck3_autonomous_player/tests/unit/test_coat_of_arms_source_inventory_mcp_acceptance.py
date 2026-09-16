from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import xar_autoplayer.coat_of_arms_dlc_sources as dlc_sources


RUNNER = (
    Path(__file__).resolve().parents[2]
    / "native_bridge"
    / "research"
    / "run_coat_of_arms_source_inventory_mcp.py"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_coat_of_arms_source_inventory_mcp",
        RUNNER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load source inventory MCP runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "MCP SDK unavailable")
class CoatOfArmsSourceInventoryMcpAcceptanceTests(
    unittest.IsolatedAsyncioTestCase
):
    async def test_collects_fixture_through_closed_official_mcp_tool(self) -> None:
        module = _load_runner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "binaries" / "ck3.exe"
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"fixture executable")
            dlc = root / "game" / "dlc" / "dlc001_fixture"
            dlc.mkdir(parents=True)
            (dlc / "fixture.dlc").write_text(
                'name="Fixture"\npath="dlc/dlc001_fixture"\n',
                encoding="utf-8",
            )
            patterns = dlc / "gfx" / "coat_of_arms" / "patterns"
            patterns.mkdir(parents=True)
            (patterns / "fixture.dds").write_bytes(b"DDS fixture")
            with patch.object(
                dlc_sources,
                "CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256",
                dlc_sources._sha256(executable),
            ):
                report = await module.collect(root)

        self.assertTrue(report["ok"])
        self.assertTrue(all(report["checks"].values()))
        self.assertEqual(report["inventory"]["installed_descriptor_count"], 1)
        self.assertEqual(report["inventory"]["coa_dds_file_count"], 1)
        self.assertFalse(
            report["inventory"]["provenance"]["engine_mount_observed"]
        )


if __name__ == "__main__":
    unittest.main()
