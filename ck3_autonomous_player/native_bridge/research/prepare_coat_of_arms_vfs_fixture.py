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
import zipfile


FIRST_SOURCE = "pattern_checkers_06.dds"
SECOND_SOURCE = "pattern_waves_01.dds"
SOLID_SOURCE = "pattern_solid.dds"
PATTERN_DIRECTORY = Path("game/gfx/coat_of_arms/patterns")
BASE_ORIGINAL_REFERENCE = "pattern_xar_vfs_base_original.dds"
BASE_MOD_REFERENCE = "pattern_xar_vfs_base_mod.dds"
ARCHIVE_SHARED = "pattern_xar_vfs_archive_shared.dds"
ARCHIVE_DIRECTORY_REFERENCE = "pattern_xar_vfs_archive_directory.dds"
ARCHIVE_LATER_REFERENCE = "pattern_xar_vfs_archive_later.dds"
REPLACED_EARLIER = "pattern_xar_vfs_replaced_earlier.dds"
REPLACE_LATER_REFERENCE = "pattern_xar_vfs_replace_later.dds"


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


def prepare_extended_fixture(
    base_profile: Path, game_directory: Path, output: Path
) -> dict[str, object]:
    """Build a base/mod and directory/archive direct-DDS precedence fixture."""

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
        mod_registry = temporary / "mod"
        mod_registry.mkdir()

        base_override_root = temporary / "coa_vfs_extended_base_override"
        base_override_patterns = (
            base_override_root / "gfx" / "coat_of_arms" / "patterns"
        )
        base_override_patterns.mkdir(parents=True)
        shutil.copy2(first_source, base_override_patterns / BASE_ORIGINAL_REFERENCE)
        shutil.copy2(second_source, base_override_patterns / FIRST_SOURCE)
        shutil.copy2(second_source, base_override_patterns / BASE_MOD_REFERENCE)
        base_manifest = base_override_patterns / "60_xar_vfs_base_override_patterns.txt"
        _write_text(
            base_manifest,
            "\n".join(
                (
                    f"{BASE_ORIGINAL_REFERENCE} = {{ colors = 2 }}",
                    f"{BASE_MOD_REFERENCE} = {{ colors = 2 }}",
                    "",
                )
            ),
        )

        directory_root = temporary / "coa_vfs_extended_archive_directory"
        directory_patterns = directory_root / "gfx" / "coat_of_arms" / "patterns"
        directory_patterns.mkdir(parents=True)
        shutil.copy2(first_source, directory_patterns / ARCHIVE_SHARED)
        shutil.copy2(first_source, directory_patterns / ARCHIVE_DIRECTORY_REFERENCE)
        directory_manifest = (
            directory_patterns / "61_xar_vfs_archive_directory_patterns.txt"
        )
        _write_text(
            directory_manifest,
            "\n".join(
                (
                    f"{ARCHIVE_SHARED} = {{ colors = 2 }}",
                    f"{ARCHIVE_DIRECTORY_REFERENCE} = {{ colors = 2 }}",
                    "",
                )
            ),
        )

        archive_path = temporary / "coa_vfs_extended_archive_later.zip"
        archive_manifest = "gfx/coat_of_arms/patterns/62_xar_vfs_archive_later_patterns.txt"
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True
        ) as archive:
            archive.writestr(
                "gfx/coat_of_arms/patterns/" + ARCHIVE_SHARED,
                second_source.read_bytes(),
            )
            archive.writestr(
                "gfx/coat_of_arms/patterns/" + ARCHIVE_LATER_REFERENCE,
                second_source.read_bytes(),
            )
            archive.writestr(
                archive_manifest,
                f"{ARCHIVE_LATER_REFERENCE} = {{ colors = 2 }}\n",
            )

        descriptors = (
            (
                "coa_vfs_extended_base_override.mod",
                "XAR CoA VFS base override fixture",
                "path",
                output / base_override_root.name,
            ),
            (
                "coa_vfs_extended_archive_directory.mod",
                "XAR CoA VFS archive directory fixture",
                "path",
                output / directory_root.name,
            ),
            (
                "coa_vfs_extended_archive_later.mod",
                "XAR CoA VFS archive later fixture",
                "archive",
                output / archive_path.name,
            ),
        )
        enabled: list[str] = []
        descriptor_receipts: list[dict[str, object]] = []
        for filename, display_name, location_key, published_location in descriptors:
            descriptor = mod_registry / filename
            _write_text(
                descriptor,
                "\n".join(
                    (
                        f'name="{display_name}"',
                        'supported_version="1.19.*"',
                        'tags={ "Graphics" }',
                        f'{location_key}="{published_location.as_posix()}"',
                        "",
                    )
                ),
            )
            registry_path = f"mod/{filename}"
            enabled.append(registry_path)
            descriptor_receipts.append(
                {
                    "registry_path": registry_path,
                    "location_kind": location_key,
                    "published_location": str(published_location.resolve()),
                    "descriptor_sha256": _sha256(descriptor),
                }
            )

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
        with zipfile.ZipFile(archive_path, "r") as archive:
            archive_entries = sorted(archive.namelist())
            archived_shared = archive.read(
                "gfx/coat_of_arms/patterns/" + ARCHIVE_SHARED
            )
            archived_reference = archive.read(
                "gfx/coat_of_arms/patterns/" + ARCHIVE_LATER_REFERENCE
            )
        receipt = {
            "schema": "ck3-coat-of-arms-vfs-extended-fixture-v1",
            "schema_version": 1,
            "purpose": "native framebuffer proof of base/mod and directory/archive direct DDS precedence",
            "predeclared_hypotheses": [
                "enabled directory mod overrides the base-game direct DDS path",
                "later enabled archive mod overrides the earlier directory-mod direct DDS path",
            ],
            "enabled_mods": enabled,
            "descriptors": descriptor_receipts,
            "load_configuration_sha256": _sha256(load_configuration),
            "pdx_settings_sha256": _sha256(temporary / "pdx_settings.txt"),
            "base_vs_mod": {
                "conflicting_resource_name": FIRST_SOURCE,
                "base_source_sha256": _sha256(first_source),
                "base_reference_name": BASE_ORIGINAL_REFERENCE,
                "base_reference_sha256": _sha256(
                    base_override_patterns / BASE_ORIGINAL_REFERENCE
                ),
                "mod_source_sha256": _sha256(second_source),
                "mod_conflict_sha256": _sha256(base_override_patterns / FIRST_SOURCE),
                "mod_reference_name": BASE_MOD_REFERENCE,
                "mod_reference_sha256": _sha256(
                    base_override_patterns / BASE_MOD_REFERENCE
                ),
                "manifest_sha256": _sha256(base_manifest),
            },
            "directory_vs_archive": {
                "conflicting_resource_name": ARCHIVE_SHARED,
                "directory_source_sha256": _sha256(first_source),
                "directory_conflict_sha256": _sha256(
                    directory_patterns / ARCHIVE_SHARED
                ),
                "directory_reference_name": ARCHIVE_DIRECTORY_REFERENCE,
                "directory_reference_sha256": _sha256(
                    directory_patterns / ARCHIVE_DIRECTORY_REFERENCE
                ),
                "directory_manifest_sha256": _sha256(directory_manifest),
                "archive_source_sha256": _sha256(second_source),
                "archive_sha256": _sha256(archive_path),
                "archive_entries": archive_entries,
                "archive_conflict_sha256": hashlib.sha256(
                    archived_shared
                ).hexdigest().upper(),
                "archive_reference_name": ARCHIVE_LATER_REFERENCE,
                "archive_reference_sha256": hashlib.sha256(
                    archived_reference
                ).hexdigest().upper(),
            },
        }
        _write_text(
            temporary / "vfs-extended-fixture-receipt.json",
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        )
        temporary.replace(output)
        return receipt
    except BaseException:
        raise


def prepare_replace_path_fixture(
    base_profile: Path, game_directory: Path, output: Path
) -> dict[str, object]:
    """Build a two-mod fixture whose later mod replaces the pattern directory."""

    base_profile = base_profile.resolve()
    game_directory = game_directory.resolve()
    output = output.resolve()
    settings = base_profile / "pdx_settings.txt"
    patterns = game_directory / PATTERN_DIRECTORY
    first_source = patterns / FIRST_SOURCE
    second_source = patterns / SECOND_SOURCE
    solid_source = patterns / SOLID_SOURCE
    if not settings.is_file():
        raise FileNotFoundError(f"base profile lacks pdx_settings.txt: {settings}")
    if not all(path.is_file() for path in (first_source, second_source, solid_source)):
        raise FileNotFoundError("exact-build replace_path fixture source DDS is missing")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    temporary = output.with_name(f".{output.name}.building-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    temporary.mkdir(parents=True)
    try:
        shutil.copy2(settings, temporary / "pdx_settings.txt")
        registry = temporary / "mod"
        registry.mkdir()

        earlier_root = temporary / "coa_vfs_replace_earlier"
        earlier_patterns = earlier_root / "gfx" / "coat_of_arms" / "patterns"
        earlier_patterns.mkdir(parents=True)
        shutil.copy2(first_source, earlier_patterns / REPLACED_EARLIER)
        earlier_manifest = earlier_patterns / "60_xar_vfs_replace_earlier_patterns.txt"
        _write_text(
            earlier_manifest,
            f"{REPLACED_EARLIER} = {{ colors = 2 }}\n",
        )

        later_root = temporary / "coa_vfs_replace_later"
        later_patterns = later_root / "gfx" / "coat_of_arms" / "patterns"
        later_patterns.mkdir(parents=True)
        shutil.copy2(solid_source, later_patterns / SOLID_SOURCE)
        shutil.copy2(second_source, later_patterns / REPLACE_LATER_REFERENCE)
        later_manifest = later_patterns / "61_xar_vfs_replace_later_patterns.txt"
        _write_text(
            later_manifest,
            "\n".join(
                (
                    f"{SOLID_SOURCE} = {{ colors = 1 }}",
                    f"{REPLACE_LATER_REFERENCE} = {{ colors = 2 }}",
                    "",
                )
            ),
        )

        descriptor_specs = (
            (
                "coa_vfs_replace_earlier.mod",
                "XAR CoA VFS replace_path earlier fixture",
                output / earlier_root.name,
                False,
            ),
            (
                "coa_vfs_replace_later.mod",
                "XAR CoA VFS replace_path later fixture",
                output / later_root.name,
                True,
            ),
        )
        enabled = []
        descriptors = []
        for filename, display_name, published_root, replaces in descriptor_specs:
            descriptor = registry / filename
            lines = [
                f'name="{display_name}"',
                'supported_version="1.19.*"',
                'tags={ "Graphics" }',
                f'path="{published_root.as_posix()}"',
            ]
            if replaces:
                lines.append('replace_path="gfx/coat_of_arms/patterns"')
            lines.append("")
            _write_text(descriptor, "\n".join(lines))
            registry_path = f"mod/{filename}"
            enabled.append(registry_path)
            descriptors.append(
                {
                    "registry_path": registry_path,
                    "published_root": str(published_root.resolve()),
                    "replace_paths": (
                        ["gfx/coat_of_arms/patterns"] if replaces else []
                    ),
                    "descriptor_sha256": _sha256(descriptor),
                }
            )

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
            "schema": "ck3-coat-of-arms-vfs-replace-path-fixture-v1",
            "schema_version": 1,
            "purpose": "native framebuffer proof that a later replace_path hides an earlier pattern directory",
            "predeclared_hypothesis": (
                "the earlier-only registered pattern behaves like a never-present missing control, "
                "and both differ from the later replacement pattern"
            ),
            "enabled_mods": enabled,
            "descriptors": descriptors,
            "replace_path": "gfx/coat_of_arms/patterns",
            "load_configuration_sha256": _sha256(load_configuration),
            "pdx_settings_sha256": _sha256(temporary / "pdx_settings.txt"),
            "earlier": {
                "resource_name": REPLACED_EARLIER,
                "source_sha256": _sha256(first_source),
                "asset_sha256": _sha256(earlier_patterns / REPLACED_EARLIER),
                "manifest_sha256": _sha256(earlier_manifest),
            },
            "later": {
                "resource_name": REPLACE_LATER_REFERENCE,
                "source_sha256": _sha256(second_source),
                "asset_sha256": _sha256(
                    later_patterns / REPLACE_LATER_REFERENCE
                ),
                "solid_source_sha256": _sha256(solid_source),
                "solid_asset_sha256": _sha256(later_patterns / SOLID_SOURCE),
                "manifest_sha256": _sha256(later_manifest),
            },
            "missing_control_name": "pattern_xar_vfs_missing_control.dds",
        }
        _write_text(
            temporary / "vfs-replace-path-fixture-receipt.json",
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        )
        temporary.replace(output)
        return receipt
    except BaseException:
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-profile", required=True, type=Path)
    parser.add_argument("--game-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--extended",
        action="store_true",
        help="build the base/mod plus directory/archive precedence fixture",
    )
    parser.add_argument(
        "--replace-path",
        action="store_true",
        help="build the later-mod pattern-directory replace_path fixture",
    )
    args = parser.parse_args()
    if args.extended and args.replace_path:
        parser.error("--extended and --replace-path are mutually exclusive")
    factory = (
        prepare_replace_path_fixture
        if args.replace_path
        else prepare_extended_fixture
        if args.extended
        else prepare_fixture
    )
    receipt = factory(args.base_profile, args.game_dir, args.output)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
