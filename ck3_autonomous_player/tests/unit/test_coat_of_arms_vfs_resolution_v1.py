from __future__ import annotations

import asyncio
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.coat_of_arms_resources import (
    CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256,
)
from xar_autoplayer.coat_of_arms_vfs_resolution import (
    CoatOfArmsVfsResolutionError,
    project_coat_of_arms_vfs_asset_winner_v1,
)


LOGICAL = "gfx/coat_of_arms/patterns/pattern_shared.dds"


def _dds(marker: int, *, width: int = 16, height: int = 8) -> bytes:
    header = bytearray(128)
    header[:4] = b"DDS "
    header[4:8] = (124).to_bytes(4, "little")
    header[12:16] = height.to_bytes(4, "little")
    header[16:20] = width.to_bytes(4, "little")
    header[28:32] = (1).to_bytes(4, "little")
    header[84:88] = b"DXT1"
    return bytes(header) + bytes([marker]) * 16


def _diagnostics(paths: list[Path]) -> dict[str, object]:
    rows = [
        {
            "ordinal": index,
            "thread_id": 10,
            "raw_result": 1,
            "success": True,
            "preview_length": len(str(path)),
            "terminated": True,
            "null_pointer": False,
            "read_fault": False,
            "path": str(path),
        }
        for index, path in enumerate(paths, start=1)
    ]
    return {
        "connected": True,
        "hello": {
            "ck3_build_match": True,
            "expected_ck3_sha256": (
                CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256
            ),
        },
        "private_observers": {
            "physfs_mounted_data_observer_v1": {
                "installed": True,
                "failure_flags": 0,
                "call_count": len(rows),
                "success_count": len(rows),
                "failure_count": 0,
                "slot_overwrite_count": 0,
                "row_count": len(rows),
                "rows": rows,
            }
        },
    }


def _write(root: Path, data: bytes) -> Path:
    target = root / Path(*LOGICAL.split("/"))
    target.parent.mkdir(parents=True)
    target.write_bytes(data)
    return target


class _Driver:
    def __init__(self, diagnostics: dict[str, object]) -> None:
        self._diagnostics = diagnostics

    def diagnostics(self) -> dict[str, object]:
        return self._diagnostics


class CoatOfArmsVfsResolutionV1Tests(unittest.TestCase):
    def _game(self, root: Path) -> Path:
        game = root / "ck3"
        executable = game / "binaries" / "ck3.exe"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"fixture")
        return game

    def _project(
        self,
        diagnostics: dict[str, object],
        game: Path,
        logical_path: str = LOGICAL,
    ) -> dict[str, object]:
        with mock.patch(
            "xar_autoplayer.coat_of_arms_vfs_resolution._sha256",
            return_value=CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256,
        ):
            return project_coat_of_arms_vfs_asset_winner_v1(
                diagnostics, str(game), logical_path
            )

    def test_later_observed_directory_mount_wins_direct_dds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = self._game(root)
            base = game / "game"
            earlier = root / "earlier"
            later = root / "later"
            first = _dds(1)
            expected = _dds(2, width=32, height=16)
            _write(base, first)
            _write(earlier, first)
            _write(later, expected)

            result = self._project(
                _diagnostics([base, earlier, later]), game
            )

            self.assertEqual(result["status"], "projected_direct_asset_winner")
            self.assertEqual(result["candidate_count"], 3)
            self.assertEqual(result["winner"]["mount_ordinal"], 3)
            self.assertEqual(result["winner"]["dds"]["width"], 32)
            self.assertFalse(result["provenance"]["engine_resolver_called"])
            self.assertEqual(
                result["provenance"]["claim_scope"],
                "direct_dds_path_winner_projection_only",
            )

    def test_later_observed_archive_mount_wins_direct_dds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = self._game(root)
            base = game / "game"
            _write(base, _dds(1))
            archive_path = root / "later.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(LOGICAL, _dds(3, width=64))

            result = self._project(
                _diagnostics([base, archive_path]), game
            )

            self.assertEqual(result["winner"]["content_kind"], "archive")
            self.assertEqual(result["winner"]["dds"]["width"], 64)

    def test_incomplete_or_truncated_live_receipt_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = self._game(root)
            base = game / "game"
            _write(base, _dds(1))
            diagnostics = _diagnostics([base])
            observer = diagnostics["private_observers"][
                "physfs_mounted_data_observer_v1"
            ]
            observer["rows"][0]["terminated"] = False
            with self.assertRaisesRegex(
                CoatOfArmsVfsResolutionError, "incomplete, truncated"
            ):
                self._project(diagnostics, game)
            observer["rows"][0]["terminated"] = True
            observer["slot_overwrite_count"] = 1
            with self.assertRaisesRegex(
                CoatOfArmsVfsResolutionError, "incomplete or lossy"
            ):
                self._project(diagnostics, game)

    def test_rejects_non_direct_or_traversing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            game = self._game(Path(directory))
            for logical in (
                "../gfx/coat_of_arms/patterns/a.dds",
                "/gfx/coat_of_arms/patterns/a.dds",
                "common/coat_of_arms/a.txt",
            ):
                with self.assertRaises(ValueError):
                    self._project({}, game, logical)

    def test_mcp_exposes_closed_live_projection_tool(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            game = self._game(root)
            base = game / "game"
            _write(base, _dds(4))
            server = create_server(_Driver(_diagnostics([base])))

            async def invoke() -> object:
                from mcp import Client

                async with Client(server) as client:
                    listed = await client.list_tools()
                    tool = {
                        item.name: item for item in listed.tools
                    }["ck3_project_coat_of_arms_vfs_asset_winner_v1"]
                    self.assertFalse(tool.input_schema["additionalProperties"])
                    with mock.patch(
                        "xar_autoplayer.coat_of_arms_vfs_resolution._sha256",
                        return_value=(
                            CK3_COAT_OF_ARMS_RESOURCE_CATALOG_V1_EXE_SHA256
                        ),
                    ):
                        return await client.call_tool(
                            "ck3_project_coat_of_arms_vfs_asset_winner_v1",
                            {
                                "game_directory": str(game),
                                "logical_path": LOGICAL,
                            },
                        )

            result = asyncio.run(invoke())
            self.assertFalse(result.is_error)
            self.assertEqual(
                result.structured_content["winner"]["mount_ordinal"], 1
            )


if __name__ == "__main__":
    unittest.main()
