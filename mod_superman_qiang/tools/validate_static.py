"""Read-only source, localization and generated-byte validation for Superman Qiang.

This structural gate never starts CK3 and does not claim native scope validity,
save compatibility or actual-game acceptance.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from product import GAME_VERSION, LANGUAGES, REPO, RUNTIME_FILES, SOURCE, VERSION, spec

sys.path.insert(0, str(REPO / "tools"))
from ck3_text_projection import blocks, masked
from independent_mod_release import sha256_file, source_errors
from translate_localization_minimax import TranslationError, assert_protected_tokens, parse_ck3_localization

# Keep product generators ahead of similarly named shared modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))

TEST_MARKERS = re.compile(
    r"(?i)\b(?:sxadt[._\w]*|sxat[._\w]*|sxad_test[._\w]*|sxad_acceptance[._\w]*|selftest|test_only|acceptance_only|XAR_ACCEPTANCE_ONLY_BEGIN|XAR_ACCEPTANCE_ONLY_END)\b"
)


def top_level_blocks(source: str):
    """Return top-level block assignments; comments/strings cannot alter depth."""
    result = []
    previous_end = 0
    for block in blocks(source):
        if block.start >= previous_end:
            result.append(block)
            previous_end = block.end
    return result


@dataclass(frozen=True)
class EffectAssignment:
    key: str
    value: str | tuple[EffectAssignment, ...]
    operator: str = "="


def effect_assignments(source: str) -> tuple[EffectAssignment, ...]:
    """Read direct assignments and nested scopes, masking comments and strings.

    This scanner checks statement order within the two skill-effect files. It
    deliberately does not attempt to validate CK3 trigger or effect grammar.
    """
    clean = masked(source)
    stack = []
    ends = {}
    for offset, character in enumerate(clean):
        if character == "{":
            stack.append(offset)
        elif character == "}":
            if not stack:
                raise ValueError(f"unmatched closing brace at {offset}")
            ends[stack.pop()] = offset + 1
    if stack:
        raise ValueError(f"unclosed brace at {stack[-1]}")
    assignment = re.compile(r"([^\s{}=<>]+)\s*(>=|<=|=|>|<)\s*(\{|[^\s{}=<>]+)")

    def read(start: int, end: int) -> tuple[EffectAssignment, ...]:
        result = []
        consumed = start
        for match in assignment.finditer(clean, start, end):
            if match.start() < consumed:
                continue
            key, operator, value = match.groups()
            if value == "{":
                consumed = ends[match.end() - 1]
                value = read(match.end(), consumed - 1)
            else:
                consumed = match.end()
            result.append(EffectAssignment(key, value, operator))
        return tuple(result)

    return read(0, len(clean))


LEDGER_SKILLS = ("diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess")
PROBE_FILE = "common/scripted_effects/sxad_probe_skill_effects.txt"
TRANSFER_FILE = "common/scripted_effects/sxad_transfer_effects.txt"
MODIFIER_FILE = "common/modifiers/sxad_skill_balance_modifiers.txt"
VALUES_FILE = "common/script_values/sxad_values.txt"


def walk_assignments(nodes, scopes=()):
    for node in nodes:
        yield scopes, node
        if isinstance(node.value, tuple):
            yield from walk_assignments(node.value, scopes + (node.key,))


def fields(nodes):
    return {node.key: node.value for node in nodes if node.operator == "="}


def evaluate_ledger_trigger(nodes, states, current="receiver") -> bool:
    """Evaluate only the declared ledger eligibility trigger subset.

    This checks generated Boolean/comparison structure with supplied values;
    it does not emulate CK3 skill/modifier semantics or a live character.
    """
    results = []
    previous_condition = False
    for node in nodes:
        key, value = node.key, node.value
        if key in {"AND", "OR", "NOT"}:
            children = [evaluate_ledger_trigger((child,), states, current) for child in value]
            results.append(all(children) if key == "AND" else any(children) if key == "OR" else not all(children))
        elif key.startswith("scope:") and isinstance(value, tuple):
            target = {"scope:sxad_donor": "donor", "scope:sxad_receiver": "receiver"}.get(key)
            if target is None:
                raise ValueError(f"unsupported ledger trigger scope: {key}")
            results.append(evaluate_ledger_trigger(value, states, target))
        elif key == "trigger_if":
            children = fields(value)
            previous_condition = evaluate_ledger_trigger(children["limit"], states, current)
            body = tuple(child for child in value if child.key != "limit")
            results.append(evaluate_ledger_trigger(body, states, current) if previous_condition else True)
        elif key == "trigger_else":
            results.append(True if previous_condition else evaluate_ledger_trigger(value, states, current))
        elif key == "has_variable":
            results.append(value in states[current]["balances"])
        elif key == "always":
            results.append(value == "yes")
        elif key == "exists":
            results.append(value in {"scope:sxad_donor", "scope:sxad_receiver"})
        elif key in LEDGER_SKILLS or key.startswith("var:sxad_"):
            left = states[current]["skills"].get(key, 0) if key in LEDGER_SKILLS else states[current]["balances"].get(key[4:], 0)
            right = int(value)
            results.append({"=": left == right, ">": left > right, "<": left < right,
                            ">=": left >= right, "<=": left <= right}[node.operator])
        else:
            raise ValueError(f"unsupported ledger trigger statement: {key}")
    return all(results)


def evaluate_ledger_value(name, definitions, balances, depth=0):
    """Evaluate guarded integer arithmetic in the generated scale values."""
    if depth > 10:
        raise ValueError("recursive ledger scale value")
    states = {role: {"skills": {}, "balances": balances} for role in ("receiver", "donor")}

    def scalar(value):
        if value.startswith("var:"):
            return balances.get(value[4:], 0)
        try:
            return int(value)
        except ValueError:
            return evaluate_ledger_value(value, definitions, balances, depth + 1)

    def calculate(nodes, total=0):
        previous_condition = False
        for node in nodes:
            if node.key == "if":
                children = fields(node.value)
                previous_condition = evaluate_ledger_trigger(children["limit"], states)
                if previous_condition:
                    total = calculate(tuple(child for child in node.value if child.key != "limit"), total)
            elif node.key == "else":
                if not previous_condition:
                    total = calculate(node.value, total)
            elif node.key == "value":
                total = scalar(node.value)
            elif node.key == "add":
                total += scalar(node.value)
            elif node.key == "subtract":
                total -= scalar(node.value)
            elif node.key == "multiply":
                total *= scalar(node.value)
            elif node.key == "min":
                total = min(total, scalar(node.value))
            elif node.key == "max":
                total = max(total, scalar(node.value))
            else:
                raise ValueError(f"unsupported ledger value statement: {node.key}")
        return total

    return calculate(definitions[name])


def ledger_contract(texts: dict[str, str]) -> dict:
    """Check conserved ledgers, bounded eligibility, scale signs and read-only UI."""
    errors = []
    for relative, source in texts.items():
        if relative.startswith("localization/"):
            continue
        try:
            if re.search(r"\badd_(?:diplomacy|martial|stewardship|intrigue|learning|prowess)_skill\s*=", masked(source)):
                errors.append(f"base skill mutation forbidden by ledger contract: {relative}")
            if relative in {"common/character_interactions/sxad_interactions.txt", "events/sxad_events.txt", VALUES_FILE}:
                if re.search(r"\b(?:set_variable|change_variable|remove_variable|add_character_modifier|remove_character_modifier|add_trait|remove_trait)\s*=", masked(source)):
                    errors.append(f"query writes persistent ledger state: {relative}")
        except ValueError as error:
            errors.append(f"invalid ledger contract source: {relative}: {error}")
    try:
        definitions = {relative: fields(effect_assignments(texts[relative]))
                       for relative in (PROBE_FILE, TRANSFER_FILE, MODIFIER_FILE, VALUES_FILE)}
        for skill in LEDGER_SKILLS:
            balance = f"sxad_{skill}_balance"
            helper = definitions[TRANSFER_FILE][f"sxad_transfer_{skill}_effect"]
            mutations = []
            initializations = []
            walked = list(walk_assignments(helper))
            for scopes, node in walk_assignments(helper):
                if node.key not in {"change_variable", "set_variable"}:
                    continue
                detail = fields(node.value)
                role = "donor" if "scope:sxad_donor" in scopes else "receiver"
                target = mutations if node.key == "change_variable" else initializations
                target.append((detail.get("name"), detail.get("add" if node.key == "change_variable" else "value"), role))
            if sorted(mutations) != sorted(((balance, "1", "receiver"), (balance, "-1", "donor"))):
                errors.append(f"ledger transfer does not conserve the same skill: {skill}")
            if sorted(initializations) != sorted(((balance, "1", "receiver"), (balance, "-1", "donor"))):
                errors.append(f"missing ledger initialization does not conserve the same skill: {skill}")
            last_write = max((i for i, (_, node) in enumerate(walked) if node.key in {"change_variable", "set_variable"}), default=-1)
            for role in ("receiver", "donor"):
                if not any(i > last_write and node.key in {f"sxad_rebuild_{skill}_modifier_effect", "sxad_rebuild_skill_modifiers_effect"}
                           and node.value == "yes" and ("donor" if "scope:sxad_donor" in scopes else "receiver") == role
                           for i, (scopes, node) in enumerate(walked)):
                    errors.append(f"ledger pair lacks modifier rebuild after both writes: {skill}: {role}")
            rebuild = definitions[PROBE_FILE][f"sxad_rebuild_{skill}_modifier_effect"]
            rebuilt = list(walk_assignments(rebuild))
            if not rebuild or rebuild[-1].key != "force_character_skill_recalculation" or rebuild[-1].value != "yes":
                errors.append(f"ledger modifier rebuild lacks final refresh: {skill}")
            for kind, point in (("gain", "1"), ("loss", "-1")):
                modifier = f"sxad_{skill}_{kind}_modifier"
                if not any(node.key == "remove_character_modifier" and node.value == modifier for _, node in rebuilt):
                    errors.append(f"ledger modifier rebuild does not remove old modifier: {modifier}")
                if not any(node.key == "add_character_modifier" and (node.value == modifier if isinstance(node.value, str)
                           else fields(node.value).get("modifier") == modifier) for _, node in rebuilt):
                    errors.append(f"ledger modifier rebuild does not apply current modifier: {modifier}")
                definition = fields(definitions[MODIFIER_FILE][modifier])
                if definition.get(skill) != point or fields(definition.get("scale", ())).get("value") != f"sxad_{skill}_{kind}_scale":
                    errors.append(f"ledger modifier skill/sign/scale mismatch: {modifier}")
                for sample in (None, -1000000, -1, 0, 1, 1000000):
                    balances = {} if sample is None else {balance: sample}
                    expected = max(0, (sample or 0) * (1 if kind == "gain" else -1))
                    if evaluate_ledger_value(f"sxad_{skill}_{kind}_scale", definitions[VALUES_FILE], balances) != expected:
                        errors.append(f"ledger scale arithmetic mismatch: {skill}: {kind}: {sample}")
            probe = definitions[PROBE_FILE][f"sxad_probe_{skill}_effect"]
            guard = next(fields(node.value)["limit"] for node in probe if node.key == "if")
            for donor_skill, receiver_skill, donor_balance, receiver_balance, expected in (
                (10, 0, None, None, True), (0, 10, None, None, False),
                (10, 0, -1000000, 0, False), (10, 0, 0, 1000000, False),
                (10, 0, -999999, 999999, True), (10, 0, 1000000, -1000000, True),
                (10, 0, 1000001, 0, False), (10, 0, 0, -1000001, False),
            ):
                states = {"donor": {"skills": {skill: donor_skill}, "balances": {} if donor_balance is None else {balance: donor_balance}},
                          "receiver": {"skills": {skill: receiver_skill}, "balances": {} if receiver_balance is None else {balance: receiver_balance}}}
                if evaluate_ledger_trigger(guard, states) != expected:
                    errors.append(f"ledger eligibility floor/capacity mismatch: {skill}: {donor_skill},{receiver_skill},{donor_balance},{receiver_balance}")
            if any(node.key in {"set_variable", "change_variable", "add_character_modifier", "remove_character_modifier"}
                   for _, node in walk_assignments(probe)):
                errors.append(f"eligibility probe changes persistent state: {skill}")
        selector = definitions[TRANSFER_FILE]["sxad_select_transfer_effect"]
        random_lists = [node.value for _, node in walk_assignments(selector) if node.key == "random_list"]
        if len(random_lists) != 1 or len(random_lists[0]) != 6 or any(node.key != "1" for node in random_lists[0]):
            errors.append("ledger random skill selection must have six equal-weight branches")
        else:
            selected = [node.key for branch in random_lists[0] for _, node in walk_assignments(branch.value)
                        if node.key.startswith("sxad_transfer_") and node.key.endswith("_effect")]
            if set(selected) != {f"sxad_transfer_{skill}_effect" for skill in LEDGER_SKILLS} or len(selected) != 6:
                errors.append("ledger random skill selection has wrong transfer helpers")
            for branch in random_lists[0]:
                helper_names = [node.key for _, node in walk_assignments(branch.value)
                                if node.key.startswith("sxad_transfer_") and node.key.endswith("_effect")]
                if len(helper_names) != 1:
                    errors.append("ledger random branch must call one transfer helper")
                    continue
                skill = helper_names[0].removeprefix("sxad_transfer_").removesuffix("_effect")
                guard = fields(branch.value).get("trigger", ())
                if not any(node.key == f"scope:sxad_can_{skill}" and node.operator == "=" and node.value == "1"
                           for _, node in walk_assignments(guard)):
                    errors.append(f"ledger random branch lacks matching eligibility flag: {skill}")
        experience = masked(texts["common/scripted_effects/sxad_experience_effects.txt"])
        if not re.search(r"var:sxad_sex_experience\s*<\s*92233720368547\b", experience):
            errors.append("experience ceiling guard changed from 92233720368547")
    except (KeyError, ValueError, TypeError, StopIteration) as error:
        errors.append(f"ledger contract structure unsupported or incomplete: {error}")
    return {"errors": errors, "skill_count": len(LEDGER_SKILLS)}


def validate(game_root: Path | None = None) -> dict:
    errors = source_errors(spec())
    hashes = []
    texts = {}
    effect_counts = {}
    for relative in sorted(RUNTIME_FILES):
        path = SOURCE / relative
        if not path.is_file():
            continue
        data = path.read_bytes()
        hashes.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if path.suffix not in {".txt", ".yml", ".mod", ".gui"}:
            continue
        try:
            source = data.decode("utf-8-sig")
            texts[relative] = source
            if TEST_MARKERS.search(source):
                errors.append(f"acceptance marker leaked into runtime: {relative}")
            if path.suffix != ".yml":
                top = top_level_blocks(source)
                keys = [block.key for block in top]
                if len(keys) != len(set(keys)):
                    errors.append(f"duplicate top-level definitions: {relative}")
                if relative.startswith("common/scripted_effects/"):
                    effect_counts[relative] = len(top)
                    if len(top) > 20:
                        errors.append(f"scripted-effect definition count exceeds 20: {relative}: {len(top)}")
        except (UnicodeError, ValueError) as error:
            errors.append(f"invalid runtime text: {relative}: {error}")
    descriptor = texts.get("descriptor.mod", "")
    if not re.search(r'(?m)^\s*version\s*=\s*"' + re.escape(VERSION) + r'"\s*$', descriptor):
        errors.append(f"descriptor version must be {VERSION}")
    if not re.search(r'(?m)^\s*supported_version\s*=\s*"1\.20(?:\.\*)?"\s*$', descriptor):
        errors.append("descriptor supported_version must be 1.20 or 1.20.*")
    if not re.search(r'(?m)^\s*picture\s*=\s*"thumbnail\.png"\s*$', descriptor):
        errors.append("descriptor picture must be thumbnail.png")
    locs = {}
    for language in LANGUAGES:
        paths = [path for path in sorted(RUNTIME_FILES) if path.startswith(f"localization/{language}/") and path.endswith(".yml")]
        values = {}
        if not paths:
            errors.append(f"missing {language} localization inventory")
        for relative in paths:
            text = texts.get(relative, "")
            if not text.splitlines() or text.splitlines()[0] != f"l_{language}:":
                errors.append(f"wrong localization header: {relative}")
            try:
                parsed = parse_ck3_localization(SOURCE / relative)
                duplicate = values.keys() & parsed.keys()
                if duplicate:
                    errors.append(f"duplicate {language} localization across files: {sorted(duplicate)}")
                values.update(parsed)
            except (OSError, TranslationError, ValueError) as error:
                errors.append(f"invalid localization: {relative}: {error}")
        locs[language] = values
    english_keys = set(locs.get("english", {}))
    baseline = locs.get("simp_chinese", {})
    for language, values in locs.items():
        if set(values) != english_keys:
            errors.append(f"localization key inventories differ: {language}")
        if baseline and values.keys() == baseline.keys():
            try:
                assert_protected_tokens(baseline, values)
            except TranslationError as error:
                errors.append(f"invalid {language} localization formatting: {error}")
        for key, value in values.items():
            for referenced in re.findall(r"\$(sxad[\w.]+)\$", value):
                if referenced not in values:
                    errors.append(f"missing localization reference {language}: {key} -> {referenced}")
    references = set()
    for relative, source in texts.items():
        if relative.startswith("localization/"):
            continue
        try:
            clean = masked(source)
            fields = "title|desc|text|custom_tooltip|notification_text|show_as_unavailable_message|greeting"
            if relative.startswith("events/"):
                fields += "|name"
            references.update(re.findall(r"\b(?:" + fields + r")\s*=\s*(sxad[\w.]+)\b", clean))
            if relative.startswith("common/traits/"):
                for block in top_level_blocks(source):
                    if block.key.startswith("sxad_"):
                        references.update((f"trait_{block.key}", f"trait_{block.key}_desc"))
        except ValueError:
            # The first pass already records the malformed source. Continue so
            # an external attempt receives a complete RED validation report.
            continue
    for language, values in locs.items():
        for referenced in sorted(references - values.keys()):
            errors.append(f"missing script localization reference {language}: {referenced}")
    ledger = ledger_contract(texts)
    errors.extend(ledger["errors"])
    generated_count = 0
    try:
        from gen_runtime import render_outputs

        expected = render_outputs(game_root)
        generated_count = len(expected)
        outside = expected.keys() - RUNTIME_FILES
        if outside:
            errors.append(f"generator output outside reviewed runtime allowlist: {sorted(outside)}")
        for relative, content in expected.items():
            path = SOURCE / relative
            if not isinstance(content, bytes):
                errors.append(f"generator did not return bytes: {relative}")
            elif not path.is_file() or path.read_bytes() != content:
                errors.append(f"generated byte parity mismatch: {relative}")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"generated runtime validation failed: {error}")
    try:
        from compose_superman_qiang_key_art import rendered_bytes

        thumbnail = SOURCE / "thumbnail.png"
        if not thumbnail.is_file() or thumbnail.read_bytes() != rendered_bytes():
            errors.append("generated byte parity mismatch: thumbnail.png")
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        errors.append(f"cover projection validation failed: {error}")
    vanilla = []
    executable_sha = None
    if game_root is not None:
        try:
            from runtime_data import EXE_SHA256, ROMANCE_SOURCE_SHA256

            relative = "common/scripted_effects/00_romance_effects.txt"
            native_root = game_root / "game" if (game_root / "game" / relative).is_file() else game_root
            source_path = native_root / relative
            source_sha = sha256_file(source_path)
            vanilla.append({"path": str(source_path), "size": source_path.stat().st_size, "sha256": source_sha})
            if source_sha != ROMANCE_SOURCE_SHA256:
                errors.append("installed romance source SHA differs from reviewed 1.20.0.3 input")
            executable = native_root.parent / "binaries" / "ck3.exe"
            executable_sha = sha256_file(executable)
            if executable_sha != EXE_SHA256:
                errors.append("installed CK3 executable SHA differs from reviewed 1.20.0.3 executable")
        except (ImportError, OSError, ValueError) as error:
            errors.append(f"installed native source validation failed: {error}")
    revision = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    return {
        "schema": "sxad.static-validation.v1", "status": "RED" if errors else "GREEN", "errors": errors,
        "git_sha": revision, "runtime_file_count": len(RUNTIME_FILES), "source_files": hashes,
        "scripted_effect_counts": effect_counts,
        "localization_key_counts": {language: len(values) for language, values in locs.items()},
        "generated_file_count": generated_count,
        "ledger_skills_checked": ledger["skill_count"],
        "vanilla_files": vanilla, "ck3_exe_sha256": executable_sha,
        "game_root": str(game_root) if game_root else None, "game_version_contract": GAME_VERSION,
        "evidence_layer": "static-structure-and-byte-contract", "ck3_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, help="optional CK3 installation or game directory for pinned source/executable SHA verification")
    parser.add_argument("--report", type=Path, help="new external evidence file; existing reports are never overwritten")
    args = parser.parse_args()
    try:
        if args.report is not None and args.report.exists():
            raise ValueError("report already exists; use a new attempt path")
        report = validate(args.game_root)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, ensure_ascii=True, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if not report["errors"] else 1
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"SXAD STATIC FAILED: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
