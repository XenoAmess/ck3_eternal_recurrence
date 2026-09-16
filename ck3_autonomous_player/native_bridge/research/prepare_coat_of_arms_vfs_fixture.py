"""Prepare an isolated two-mod CK3 CoA VFS precedence fixture.

The output is a source profile for the managed frontend acceptance runner.  It
contains two enabled directory mods.  Both provide the same DDS path, while
each also provides a unique reference path with byte-identical content.  A
single native session can therefore determine the conflict winner without
changing load order or relying on screenshots/OCR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil


FIRST_SOURCE = "pattern_checkers_06.dds"
SECOND_SOURCE = "pattern_waves_01.dds"
PATTERN_DIRECTORY = Path("game/gfx/coat_of_arms/patterns")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def _write_mod(
    profile: Path,
    published_profile: Path,
    *,
    key: str,
    display_name: str,
    source_dds: Path,
    reference_name: str,
    manifest_name: str,
) -> dict[str, object]:
    content = profile / f"coa_vfs_fixture_{key}"
    published_content = published_profile / f"coa_vfs_fixture_{key}"
    patterns = content / "gfx" / "coat_of_arms" / "patterns"
    patterns.mkdir(parents=True)
    shared = patterns / "pattern_xar_vfs_shared.dds"
    reference = patterns / reference_name
    shutil.copy2(source_dds, shared)
    shutil.copy2(source_dds, reference)
    manifest = patterns / manifest_name
    _write_text(
        manifest,
        "\n".join(
            (
                "pattern_xar_vfs_shared.dds = { colors = 2 }",
                f"{reference_name} = {{ colors = 2 }}",
                "",
            )
        ),
    )
    descriptor = profile / "mod" / f"coa_vfs_fixture_{key}.mod"
    _write_text(
        descriptor,
        "\n".join(
            (
                f'name="{display_name}"',
                'supported_version="1.19.*"',
                'tags={ "Graphics" }',
                f'path="{published_content.as_posix()}"',
                "",
            )
        ),
    )
    return {
        "key": key,
        "display_name": display_name,
        "registry_path": f"mod/{descriptor.name}",
        "descriptor_path": str(
            (published_profile / "mod" / descriptor.name).resolve()
        ),
        "descriptor_sha256": _sha256(descriptor),
        "content_root": str(published_content.resolve()),
        "manifest_path": str(
            (published_content / "gfx" / "coat_of_arms" / "patterns" / manifest.name).resolve()
        ),
        "manifest_sha256": _sha256(manifest),
        "source_dds_path": str(source_dds.resolve()),
        "source_dds_sha256": _sha256(source_dds),
        "shared_dds_sha256": _sha256(shared),
        "reference_name": reference_name,
        "reference_dds_sha256": _sha256(reference),
    }


def prepare_fixture(base_profile: Path, game_directory: Path, output: Path) -> dict[str, object]:
    base_profile = base_profile.resolve()
    game_directory = game_directory.resolve()
    output = output.resolve()
    settings = base_profile / "pdx_settings.txt"
    patterns = game_directory / PATTERN_DIRECTORY
    first_source = patterns / FIRST_SOURCE
    second_source = patterns / SECOND_SOURCE
    if not settings.is_file():
        raise FileNotFoundError(f"base profile lacks pdx_settings.txt: {settings}")
    if not first_source.is_file() or not second_source.is_file():
        raise FileNotFoundError("exact-build VFS fixture source DDS is missing")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    temporary = output.with_name(f".{output.name}.building-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    temporary.mkdir(parents=True)
    try:
        shutil.copy2(settings, temporary / "pdx_settings.txt")
        (temporary / "mod").mkdir()
        first = _write_mod(
            temporary,
            output,
            key="first",
            display_name="XAR CoA VFS fixture load order 0",
            source_dds=first_source,
            reference_name="pattern_xar_vfs_first.dds",
            manifest_name="50_xar_vfs_first_patterns.txt",
        )
        second = _write_mod(
            temporary,
            output,
            key="second",
            display_name="XAR CoA VFS fixture load order 1",
            source_dds=second_source,
            reference_name="pattern_xar_vfs_second.dds",
            manifest_name="51_xar_vfs_second_patterns.txt",
        )
        enabled = [first["registry_path"], second["registry_path"]]
        load_configuration = temporary / "dlc_load.json"
        load_configuration.write_text(
            json.dumps(
                {"enabled_mods": enabled, "disabled_dlcs": []},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
            newline="\n",
        )
        receipt = {
            "schema": "ck3-coat-of-arms-vfs-fixture-v1",
            "schema_version": 1,
            "purpose": "native framebuffer proof of a conflicting direct DDS path",
            "predeclared_hypothesis": "enabled_mods load order 1 wins",
            "shared_resource_name": "pattern_xar_vfs_shared.dds",
            "enabled_mods": enabled,
            "load_configuration_sha256": _sha256(load_configuration),
            "pdx_settings_sha256": _sha256(temporary / "pdx_settings.txt"),
            "mods": [first, second],
        }
        _write_text(
            temporary / "vfs-fixture-receipt.json",
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        )
        temporary.replace(output)
        return receipt
    except BaseException:
        # Preserve a failed build for diagnosis; never rewrite it as a valid fixture.
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-profile", required=True, type=Path)
    parser.add_argument("--game-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    receipt = prepare_fixture(args.base_profile, args.game_dir, args.output)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
