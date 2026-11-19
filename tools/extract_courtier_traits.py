#!/usr/bin/env python3
"""Extract the vanilla trait metadata used by the courtier creator generator."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from ck3_installation import configured_game_dir
from gen_vivhite_courtier import TraitMetadata, is_trait_metadata


ROOT = Path(__file__).resolve().parent.parent
GAME_VERSION = "1.20.0.3"  # Historical default output identity, never inferred from the current installation.
REVIEWED_SOURCE_SHA256 = {
    "1.20.0.3": "93ad0316b733aa474d34841bd92fb3fc9336c111e9f06e7910178e74482185aa",
    "1.21.0.3": "793718c2388f8d7b6c009468a2f5f8f5d1d8443acec4a015614ffac4f05b98cd",
}
DEFAULT_SOURCE = (
    configured_game_dir(ROOT) / "game" / "common" / "traits" / "00_traits.txt"
)
DEFAULT_OUTPUT = Path(__file__).resolve().with_name("courtier_traits_1_20_0_3.json")

# The shipped source uses the first spelling. _traits.info documents the second.
GROUP_EQUIVALENCE_KEYS = {"group_equivalence", "group_equivelence"}
SCALAR_FIELDS = {
    "category",
    "physical",
    "shown_in_ruler_designer",
    "ruler_designer_cost",
    "minimum_age",
    "maximum_age",
    "valid_sex",
    "group",
    "level",
}


@dataclass(frozen=True)
class Token:
    value: str
    line: int


def tokenize(text: str) -> list[Token]:
    """Tokenize Paradox script while ignoring comments and quoted braces."""
    tokens: list[Token] = []
    index = 0
    line = 1
    operator_chars = "=<>!?"
    delimiters = set("{}#\"") | set(operator_chars)

    while index < len(text):
        char = text[index]
        if char.isspace():
            if char == "\n":
                line += 1
            index += 1
            continue
        if char == "#":
            newline = text.find("\n", index)
            if newline == -1:
                break
            index = newline
            continue
        if char in "{}":
            tokens.append(Token(char, line))
            index += 1
            continue
        if char == '"':
            start_line = line
            index += 1
            value: list[str] = []
            while index < len(text):
                char = text[index]
                if char == '"':
                    index += 1
                    break
                if char == "\\":
                    if index + 1 >= len(text):
                        raise ValueError(
                            f"unterminated escape in string starting on line {start_line}"
                        )
                    escaped = text[index + 1]
                    value.append(escaped)
                    if escaped == "\n":
                        line += 1
                    index += 2
                    continue
                if char == "\n":
                    line += 1
                value.append(char)
                index += 1
            else:
                raise ValueError(f"unterminated string starting on line {start_line}")
            tokens.append(Token("".join(value), start_line))
            continue
        if char in operator_chars:
            start = index
            while index < len(text) and text[index] in operator_chars:
                index += 1
            tokens.append(Token(text[start:index], line))
            continue

        start = index
        while (
            index < len(text)
            and not text[index].isspace()
            and text[index] not in delimiters
        ):
            index += 1
        if start == index:
            raise ValueError(f"cannot tokenize {text[index]!r} on line {line}")
        tokens.append(Token(text[start:index], line))

    return tokens


def matching_brace(tokens: list[Token], opening: int) -> int:
    if tokens[opening].value != "{":
        raise ValueError(f"expected opening brace on line {tokens[opening].line}")
    depth = 0
    for index in range(opening, len(tokens)):
        if tokens[index].value == "{":
            depth += 1
        elif tokens[index].value == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unclosed brace starting on line {tokens[opening].line}")


def top_level_blocks(tokens: list[Token]) -> list[tuple[str, list[Token]]]:
    blocks: list[tuple[str, list[Token]]] = []
    index = 0
    while index < len(tokens):
        key = tokens[index]
        if key.value in {"{", "}"}:
            raise ValueError(f"unexpected {key.value!r} on line {key.line}")
        if index + 2 >= len(tokens) or tokens[index + 1].value != "=":
            raise ValueError(f"expected assignment after {key.value!r} on line {key.line}")

        value = tokens[index + 2]
        if value.value != "{":
            index += 3
            continue
        closing = matching_brace(tokens, index + 2)
        if not key.value.startswith("@"):
            blocks.append((key.value, tokens[index + 3 : closing]))
        index = closing + 1
    return blocks


def list_values(tokens: list[Token], field: str, line: int) -> list[str]:
    values: list[str] = []
    depth = 0
    for token in tokens:
        if token.value == "{":
            depth += 1
        elif token.value == "}":
            depth -= 1
        elif depth == 0:
            if token.value in {"=", "?=", ">=", "<=", "!=", "=="}:
                raise ValueError(f"unexpected operator in {field!r} on line {line}")
            values.append(token.value)
    return values


def direct_metadata(tokens: list[Token], trait_key: str) -> dict[str, object]:
    values: dict[str, object] = {}
    has_track = False
    index = 0

    while index < len(tokens):
        field = tokens[index]
        if index + 1 >= len(tokens) or tokens[index + 1].value != "=":
            index += 1
            continue
        if index + 2 >= len(tokens):
            raise ValueError(
                f"missing value for {field.value!r} in {trait_key!r} on line {field.line}"
            )

        value = tokens[index + 2]
        canonical = (
            "group_equivalence"
            if field.value in GROUP_EQUIVALENCE_KEYS
            else field.value
        )
        if value.value == "{":
            closing = matching_brace(tokens, index + 2)
            if field.value == "opposites":
                if "opposites" in values:
                    raise ValueError(f"duplicate opposites field in {trait_key!r}")
                values["opposites"] = list_values(
                    tokens[index + 3 : closing], field.value, field.line
                )
            elif field.value in {"track", "tracks"}:
                has_track = True
            index = closing + 1
            continue

        if canonical in SCALAR_FIELDS or canonical == "group_equivalence":
            if canonical in values:
                raise ValueError(f"duplicate {canonical!r} field in {trait_key!r}")
            values[canonical] = value.value
        index += 3

    values["has_track"] = has_track
    return values


def parse_bool(value: object, field: str, trait_key: str) -> bool:
    if value == "yes":
        return True
    if value == "no":
        return False
    raise ValueError(f"{trait_key!r} has invalid {field} value {value!r}")


def parse_optional_int(value: object, field: str, trait_key: str) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value), 10)
    except ValueError as error:
        raise ValueError(
            f"{trait_key!r} has non-integer {field} value {value!r}"
        ) from error


def extract_traits(text: str) -> list[TraitMetadata]:
    traits: list[TraitMetadata] = []
    seen: set[str] = set()
    for key, body in top_level_blocks(tokenize(text)):
        if key in seen:
            raise ValueError(f"duplicate top-level trait {key!r}")
        seen.add(key)
        raw = direct_metadata(body, key)
        raw_opposites = raw.get("opposites", [])
        if not isinstance(raw_opposites, list) or not all(isinstance(item, str) for item in raw_opposites):
            raise ValueError(f"{key!r} has invalid opposites metadata")
        opposites = list(dict.fromkeys(raw_opposites))
        trait: dict[str, object] = {
                "key": key,
                "category": raw.get("category"),
                "physical": parse_bool(raw.get("physical", "no"), "physical", key),
                "shown_in_ruler_designer": parse_bool(
                    raw.get("shown_in_ruler_designer", "yes"),
                    "shown_in_ruler_designer",
                    key,
                ),
                "ruler_designer_cost": parse_optional_int(
                    raw.get("ruler_designer_cost", "0"),
                    "ruler_designer_cost",
                    key,
                ),
                "minimum_age": parse_optional_int(raw.get("minimum_age"), "minimum_age", key),
                "maximum_age": parse_optional_int(raw.get("maximum_age"), "maximum_age", key),
                "valid_sex": raw.get("valid_sex", "all"),
                "group": raw.get("group"),
                "group_equivalence": raw.get("group_equivalence"),
                "opposites": opposites,
                "level": parse_optional_int(raw.get("level"), "level", key),
                "has_track": raw["has_track"],
        }
        if not is_trait_metadata(trait):
            raise ValueError(f"{key!r} has invalid typed trait metadata")
        traits.append(trait)
    return traits


def source_label(path: Path) -> str:
    resolved = path.resolve()
    if (resolved == DEFAULT_SOURCE.resolve()
            or resolved.parts[-4:] == ("game", "common", "traits", "00_traits.txt")):
        # A local junction may point outside the checkout. Snapshot identity
        # uses the logical game path, independent of the installation directory.
        return "Crusader Kings III/game/common/traits/00_traits.txt"
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def validate_reviewed_output(game_version: str, source_sha256: str, output: Path, *, explicit_output: bool) -> None:
    """Review exact source bytes and protect the old metadata files before any write."""
    if game_version not in REVIEWED_SOURCE_SHA256 or source_sha256 != REVIEWED_SOURCE_SHA256[game_version]:
        raise ValueError("source SHA256 does not match the explicitly reviewed game version")
    historical = {DEFAULT_OUTPUT.with_name(name).resolve() for name in (
        "courtier_traits_1_19_0_6.json", "courtier_traits_1_20_0_2.json", "courtier_traits_1_20_0_3.json")}
    if game_version != GAME_VERSION and (not explicit_output or output.resolve() in historical):
        raise ValueError("new game version requires an explicit nonhistorical output; historical default is protected")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_path", nargs="?", type=Path)
    parser.add_argument("output_path", nargs="?", type=Path)
    parser.add_argument("--source", dest="source_option", type=Path)
    parser.add_argument("--output", dest="output_option", type=Path)
    parser.add_argument("--game-version", required=True, choices=tuple(REVIEWED_SOURCE_SHA256), help="explicit reviewed source identity; never inferred from installed files")
    args = parser.parse_args()
    if args.source_path is not None and args.source_option is not None:
        parser.error("source may be supplied either positionally or with --source, not both")
    if args.output_path is not None and args.output_option is not None:
        parser.error("output may be supplied either positionally or with --output, not both")
    return args


def main() -> int:
    args = parse_args()
    source = args.source_option or args.source_path or DEFAULT_SOURCE
    output = args.output_option or args.output_path or DEFAULT_OUTPUT

    source_bytes = source.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    validate_reviewed_output(args.game_version, source_sha256, output, explicit_output=args.output_option is not None or args.output_path is not None)
    traits = extract_traits(source_bytes.decode("utf-8-sig"))
    snapshot = {
        "schema_version": 1,
        "source": {
            "game_version": args.game_version,
            "file": source_label(source),
            "sha256": source_sha256,
        },
        "trait_count": len(traits),
        "traits": traits,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"extracted {len(traits)} traits from CK3 {args.game_version}; "
        f"sha256={source_sha256}"
    )
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
