"""Real release/copy/JSON/host consumers; preflight bytes grant no live credit."""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Protocol, runtime_checkable
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / "tools"), str(REPO / "ck3_autonomous_player/src"), str(REPO / "mod_living_artifacts/tools")]
from independent_mod_release import ProductSpec, build
from ck3_mod_acceptance_saved_profile_v2 import MaterializedSavedProfile, materialize_saved_profile_v2, write_saved_profile_inventory_v2
from xar_autoplayer.saved_campaign_profile_inventory_v2 import Role, parse_inventory, verify_inventory


@dataclass(frozen=True)
class ProfileSpec:
    profile_dir: Path
    state_dir: Path


@runtime_checkable
class PrepareCampaign(Protocol):
    def __call__(self, args: argparse.Namespace, spec: ProfileSpec) -> object: ...


@runtime_checkable
class ProductSource(Protocol):
    def spec(self) -> ProductSpec: ...


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Expected test boundary object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Expected string fields")
        result[key] = item
    return result


def actual_host_preparer() -> PrepareCampaign:
    host = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
    tree = ast.parse(host.read_text(encoding="utf-8-sig"))
    names = {"saved_campaign_expected", "prepare_saved_campaign", "file_sha"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise ValueError("Actual host production scope missing")
    scope: dict[str, object] = {"argparse": argparse, "Path": Path, "json": json, "re": re, "hashlib": hashlib}
    body: list[ast.stmt] = list(nodes)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(host), "exec"), scope)
    prepare = scope["prepare_saved_campaign"]
    if not isinstance(prepare, PrepareCampaign):
        raise ValueError("Actual host preparer unavailable")
    return prepare


class SavedProfileV2Tests(unittest.TestCase):
    stage_temp: tempfile.TemporaryDirectory[str]
    staging: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.stage_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.stage_temp.cleanup)
        source = REPO / "mod_living_artifacts/tools/product.py"
        spec = importlib.util.spec_from_file_location("saved_profile_actual_formal_product", source)
        if spec is None or spec.loader is None:
            raise ValueError("Actual formal product definition unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        candidate: object = module
        if not isinstance(candidate, ProductSource):
            raise ValueError("Actual product spec contract missing")
        # Actual common release projection, without installed CK3 or validation
        # credit. No handwritten substitute for the formal bootstrap is used.
        revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
        cls.staging = build(candidate.spec(), Path(cls.stage_temp.name) / "formal", revision)[0]
        if "on_game_start_after_lobby" not in (cls.staging / "common/on_action/xalw_core.txt").read_text(encoding="utf-8-sig"):
            raise ValueError("Actual formal bootstrap disappeared")

    def make(self, root: Path, role: Role | None) -> tuple[argparse.Namespace, ProfileSpec, MaterializedSavedProfile]:
        configs: dict[str, dict[str, object]] = {}
        for index, name in enumerate(("pdx_settings.txt", "tutorial.txt", "presets.txt", "player/game_rules/presets.txt")):
            path = root / "inputs" / str(index)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"AUTHORED CONFIGURATION; NOT A GAME RUN\n")
            configs[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        prepared = materialize_saved_profile_v2({"state_dir": str(root / "state"), "output": str(root / "prepared")},
            None if role is None else self.staging, configs, source_role=role)
        source = root / "authored-preflight-input.ck3"
        source.write_bytes(b"AUTHORED PREFLIGHT BYTES ONLY; NEVER LOADED IN CK3\n")
        args = argparse.Namespace(saved_campaign_save=source, saved_campaign_save_bytes=source.stat().st_size,
            saved_campaign_save_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), saved_campaign_player_id=31254,
            saved_campaign_date_raw=53144328, saved_campaign_product_inventory=Path(prepared["product_inventory"]["path"]))
        return args, ProfileSpec(Path(prepared["profile"]), Path(prepared["state_dir"])), prepared

    def test_actual_formal_release_bootstrap_reaches_real_host_and_copy_readback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            args, spec, prepared = self.make(Path(temporary), "formal_product")
            value: object = json.loads(Path(prepared["product_inventory"]["path"]).read_bytes())
            inventory = parse_inventory(value)
            self.assertEqual(parse_inventory(json.loads(json.dumps(inventory.to_json()))), inventory)
            self.assertEqual(verify_inventory(inventory, profile=spec.profile_dir, actual_enabled_mods=["mod/product.mod"]), inventory)
            result = mapping(actual_host_preparer()(args, spec))
            self.assertEqual(Path(str(result["copied_save_path"])).read_bytes(), Path(args.saved_campaign_save).read_bytes())
            self.assertEqual(result["status"], "IMMUTABLE_SAVE_COPIED_TO_FRESH_PRODUCT_ONLY_PROFILE")
            self.assertIs(result["product_acceptance_proven"], False)

    def test_actual_bootstrap_bytes_classified_as_fixture_or_overlay_reach_real_refusal(self) -> None:
        for role in ("case_fixture", "case_overlay"):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                selected: Role = "case_fixture" if role == "case_fixture" else "case_overlay"
                args, spec, _ = self.make(Path(temporary), selected)
                with self.assertRaisesRegex(ValueError, "fixture/overlay contains a cold-start registrar"):
                    actual_host_preparer()(args, spec)
                self.assertFalse((spec.profile_dir / "save games").exists())

    def test_explicit_vanilla_v2_reaches_actual_host(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            args, spec, _ = self.make(Path(temporary), None)
            result = mapping(actual_host_preparer()(args, spec))
            self.assertEqual(result["status"], "IMMUTABLE_SAVE_COPIED_TO_FRESH_VANILLA_PROFILE")
            self.assertIs(result["source_game_state_claimed"], False)

    def test_wrong_file_integer_types_are_rejected_by_actual_host_before_copy(self) -> None:
        invalid: tuple[object, ...] = (True, False, 1.0, "1", None)
        for index, wrong in enumerate(invalid):
            with self.subTest(value=wrong), tempfile.TemporaryDirectory() as temporary:
                args, spec, prepared = self.make(Path(temporary) / str(index), "formal_product")
                path = Path(prepared["product_inventory"]["path"])
                value = mapping(json.loads(path.read_bytes()))
                files = value["product_files"]
                if not isinstance(files, list):
                    self.fail("Actual producer file list absent")
                first = mapping(files[0]); first["bytes"] = wrong
                files[0] = first
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "File bytes must be an exact bounded integer"):
                    actual_host_preparer()(args, spec)
                self.assertFalse((spec.profile_dir / "save games").exists())

    def test_missing_null_extra_and_legacy_inventory_are_not_v2_aliases(self) -> None:
        for changed in ("missing", "null", "extra", "legacy"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                args, spec, prepared = self.make(Path(temporary), "formal_product")
                path = Path(prepared["product_inventory"]["path"])
                value = mapping(json.loads(path.read_bytes()))
                if changed == "missing":
                    del value["projections"]
                elif changed == "null":
                    value["projections"] = None
                elif changed == "extra":
                    value["role_alias"] = "formal_product"
                else:
                    value["schema"] = "ck3-saved-campaign-product-only-profile-v1"
                    del value["profile_mode"]
                    del value["projections"]
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    actual_host_preparer()(args, spec)
                self.assertFalse((spec.profile_dir / "save games").exists())

    def test_unknown_role_and_duplicate_or_wrong_projection_are_rejected_by_host(self) -> None:
        changes: tuple[object, ...] = (True, None, [], "product", "FORMAL_PRODUCT", "duplicate", "wrong-root")
        for changed in changes:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                args, spec, prepared = self.make(Path(temporary), "formal_product")
                path = Path(prepared["product_inventory"]["path"])
                value = mapping(json.loads(path.read_bytes()))
                projections = value["projections"]
                if not isinstance(projections, list):
                    self.fail("Actual producer projection list absent")
                first = mapping(projections[0])
                if changed == "duplicate":
                    projections.append(dict(first))
                elif changed == "wrong-root":
                    first["root_path"] = str(self.staging)
                    projections[0] = first
                else:
                    first["source_role"] = changed
                    projections[0] = first
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    actual_host_preparer()(args, spec)
                self.assertFalse((spec.profile_dir / "save games").exists())

    def test_missing_extra_duplicate_and_changed_file_pins_fail_real_closure(self) -> None:
        for changed in ("missing", "extra", "duplicate", "changed"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                args, spec, prepared = self.make(root, "formal_product")
                path = Path(prepared["product_inventory"]["path"])
                value = mapping(json.loads(path.read_bytes()))
                files = value["product_files"]
                if not isinstance(files, list):
                    self.fail("Actual producer file list absent")
                if changed == "missing":
                    files.pop()
                elif changed == "duplicate":
                    files.append(files[0])
                elif changed == "changed":
                    first = mapping(files[0]); first["sha256"] = "0" * 64
                    files[0] = first
                else:
                    unrelated = root / "unrelated.txt"
                    unrelated.write_bytes(b"not an enabled product file")
                    files.append({"path": str(unrelated), "bytes": unrelated.stat().st_size,
                        "sha256": hashlib.sha256(unrelated.read_bytes()).hexdigest()})
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    actual_host_preparer()(args, spec)
                self.assertFalse((spec.profile_dir / "save games").exists())

    def test_formal_projection_cannot_launder_a_second_overlay_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args, spec, prepared = self.make(root, "formal_product")
            original = parse_inventory(json.loads(Path(prepared["product_inventory"]["path"]).read_bytes()))
            overlay = spec.profile_dir / "mod-content/other-content"
            overlay.mkdir()
            script = overlay / "initialization.txt"
            script.write_text("on_game_start_after_lobby = { on_actions = { authored_setup } }\n", encoding="utf-8")
            outer = spec.profile_dir / "mod/other.mod"
            outer.write_text('path="' + overlay.as_posix() + '"\n', encoding="utf-8")
            files = [row.to_json() for row in original.files]
            files.extend({"path": str(path), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                for path in (outer, script))
            enabled = ["mod/product.mod", "mod/other.mod"]
            inventory = root / "mixed-v2.json"
            write_saved_profile_inventory_v2(inventory, profile=spec.profile_dir, mode="enabled", enabled_mods=enabled,
                product_files=files, roles={"mod/product.mod": "formal_product", "mod/other.mod": "case_overlay"})
            (spec.profile_dir / "dlc_load.json").write_text(json.dumps({"enabled_mods": enabled}), encoding="utf-8")
            args.saved_campaign_product_inventory = inventory
            with self.assertRaisesRegex(ValueError, "fixture/overlay contains a cold-start registrar"):
                actual_host_preparer()(args, spec)
            self.assertFalse((spec.profile_dir / "save games").exists())


if __name__ == "__main__":
    unittest.main()
