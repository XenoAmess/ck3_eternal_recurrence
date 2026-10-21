"""Deterministically project reviewed gameplay sources into CK3 runtime files."""
from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import re
import sys

from living_artifacts_model import Language, RuntimeInventory, SourcePatch
from product import SOURCE, REPO, VERSION

sys.path.append(str(REPO / "tools"))
from ck3_text_projection import blocks, normalize, project, recover

BOM = b"\xef\xbb\xbf"


def split_definitions(text: str, stem: str, maximum: int = 10) -> dict[str, str]:
    """Keep effect files small, preserving complete top-level definitions."""
    source = normalize(text)
    all_blocks = blocks(source)
    top = [block for block in all_blocks if not any(
        parent.opening < block.start < parent.end for parent in all_blocks
    )]
    if not top:
        raise ValueError(f"Generator produced no definitions for {stem}")
    result: dict[str, str] = {}
    for start in range(0, len(top), maximum):
        selection = top[start:start + maximum]
        result[f"common/scripted_effects/{stem}_{start // maximum + 1:02}.txt"] = (
            "# Generated; edit tools, then run generate.py.\n" +
            "\n\n".join(source[block.start:block.end] for block in selection) + "\n"
        )
    return result


def merge_localization(*sources: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for source in sources:
        duplicate = result.keys() & source.keys()
        if duplicate:
            raise ValueError(f"Duplicate localization keys: {sorted(duplicate)}")
        result.update(source)
    return result


def render_localization(language: str, entries: dict[str, str]) -> str:
    lines = [f"l_{language}:"]
    for key, value in sorted(entries.items()):
        if not key.startswith(("xalw_", "xalw.", "rule_xalw_", "setting_xalw_")) or "\r" in value:
            raise ValueError(f"Invalid generated localization entry: {key}")
        escaped = value.replace('"', '\\"').replace("\n", "\\n")
        lines.append(f' {key}:0 "{escaped}"')
    return "\n".join(lines) + "\n"


def apply_source_patches(game: Path, patches: tuple[SourcePatch, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for patch in patches:
        if patch.relative_path in result:
            raise ValueError("Multiple patches target one file; combine them in one shared contract")
        source = (game / patch.relative_path).read_text(encoding="utf-8-sig")
        output = project(source, patch.expected_normalized_sha256, list(patch.replacements))
        if recover(output, patch.expected_normalized_sha256, list(patch.replacements)) != normalize(source):
            raise ValueError("Source patch did not round-trip")
        if patch.relative_path.startswith("common/scripted_effects/"):
            stem = "xalw_native_" + Path(patch.relative_path).stem
            chunks = split_definitions(output, stem)
            constants = "\n".join(re.findall(r"(?m)^\s*@[A-Za-z0-9_]+\s*=\s*[^\n]+", output))
            if constants:
                chunks = {path: constants + "\n" + text for path, text in chunks.items()}
            result[patch.relative_path] = "# Original source definitions are preserved in generated " + stem + "_* groups.\n"
            result.update(chunks)
        else:
            result[patch.relative_path] = output
    return result


def render_files(game: Path) -> dict[str, bytes]:
    import living_artifacts_core as core
    import living_artifacts_content as content

    renderers: tuple[tuple[str, Callable[[], str]], ...] = (
        ("common/on_action/xalw_core.txt", core.render_core_on_actions),
        ("common/on_action/xalw_content.txt", content.render_content_on_actions),
        ("common/scripted_triggers/xalw_triggers.txt", core.render_core_triggers),
        ("common/script_values/xalw_values.txt", core.render_core_script_values),
        ("common/customizable_localization/xalw_artifacts.txt", core.render_core_custom_localization),
        ("common/game_rules/xalw_rules.txt", core.render_core_game_rules),
        ("common/decisions/xalw_decisions.txt", core.render_core_decisions),
        ("common/character_interactions/xalw_interactions.txt", core.render_core_interactions),
        ("common/modifiers/xalw_core_modifiers.txt", core.render_core_modifiers),
        ("common/modifiers/xalw_content_modifiers.txt", content.render_content_modifiers),
        ("common/opinion_modifiers/xalw_content_opinions.txt", content.render_content_opinions),
        ("events/xalw_core_events.txt", core.render_core_events),
        ("events/xalw_content_events.txt", content.render_content_events),
    )
    texts = {path: render() for path, render in renderers}
    texts.update(split_definitions(core.render_core_effects(), "xalw_core"))
    texts.update(split_definitions(content.render_content_effects(), "xalw_content"))
    texts.update(apply_source_patches(game, core.get_core_patches(game) + content.get_content_patches(game)))
    languages: tuple[Language, ...] = ("simp_chinese", "english")
    for typed_language in languages:
        entries = merge_localization(core.render_core_localization(typed_language), content.render_content_localization(typed_language))
        texts[f"localization/{typed_language}/xalw_l_{typed_language}.yml"] = render_localization(typed_language, entries)
    texts["descriptor.mod"] = (
        f'version="{VERSION}"\n'
        'tags={ "Artifacts" "Events" "Gameplay" }\n'
        'name="活武器：饥渴的传世之物 / Living Artifacts"\n'
        'supported_version="1.20.*"\n'
        'picture="thumbnail.png"\n'
    )
    return {path: (b"" if path == "descriptor.mod" else BOM) + normalize(value).encode("utf-8") for path, value in texts.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True, help="CK3 game/ script root inside the installation")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--review-inventory", action="store_true", help="Write the explicit release inventory for review")
    args = parser.parse_args()
    files = render_files(args.game)
    errors: list[str] = []
    for relative, data in files.items():
        path = SOURCE / relative
        if args.check:
            if not path.is_file() or path.read_bytes() != data:
                errors.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if errors:
        print(json.dumps({"status": "FAIL", "changed_generated_files": errors}))
        return 1
    if args.review_inventory:
        paths = set(files) | {"thumbnail.png"}
        # Other publication languages are reviewed, format-certified source files.
        paths.update(f"localization/{language}/xalw_l_{language}.yml" for language in (
            "french", "german", "japanese", "korean", "polish", "russian", "spanish",
        ))
        inventory = RuntimeInventory.parse({"schema_version": 1, "paths": sorted(paths)})
        (SOURCE / "docs/runtime-inventory.json").write_text(json.dumps(inventory.to_json(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "generated_files": len(files), "checked": args.check}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
