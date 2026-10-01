#!/usr/bin/env python3
"""Compare frozen reviewed event bodies against CK3 1.20.0.2, file-only.

This is lexical compatibility evidence, not a live acceptance or a proof that
all scripted dependencies, native triggers or caller chains retain semantics.
Comments and whitespace are ignored; quoted strings, escaping, token ordering
and repeated field ordering are preserved. General religion is owner-deferred.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import difflib
import hashlib
import json
from pathlib import Path
from typing import Iterable


NEW_BUILD = "1.20.0.2"
NEW_EXE_SHA256 = "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
OLD_BUILD = "1.19.0.6"
EXCLUDED = {
    "fervor.1002": "owner-deferred-general-religion",
    "court_chaplain_task.0313": "owner-deferred-general-religion",
    "great_holy_war.0011": "war-domain-outside-nonwar-work-package",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class Token:
    value: str
    offset: int
    end: int
    line: int


def tokenize(text: str) -> list[Token]:
    """Keep raw quoted text, including quote marks and escaped characters."""
    result: list[Token] = []
    position = 0
    line = 1
    operators = "=<>!?"
    delimiters = set('{}#"') | set(operators)
    while position < len(text):
        character = text[position]
        if character.isspace() or character == "\ufeff":
            line += character == "\n"
            position += 1
            continue
        if character == "#":
            end = text.find("\n", position)
            position = len(text) if end == -1 else end
            continue
        start, start_line = position, line
        if character == '"':
            position += 1
            while position < len(text):
                character = text[position]
                if character == "\\" and position + 1 < len(text):
                    line += text[position + 1] == "\n"
                    position += 2
                elif character == '"':
                    position += 1
                    break
                else:
                    line += character == "\n"
                    position += 1
            else:
                raise ValueError(f"Unterminated quoted string on line {start_line}")
        elif character in "{}":
            position += 1
        elif character in operators:
            while position < len(text) and text[position] in operators:
                position += 1
        else:
            while (position < len(text) and not text[position].isspace()
                   and text[position] not in delimiters):
                position += 1
        result.append(Token(text[start:position], start, position, start_line))
    return result


def assignments(tokens: list[Token]) -> list[tuple[str, list[Token]]]:
    """Extract depth-zero assignments; retain duplicate fields and ordering."""
    result: list[tuple[str, list[Token]]] = []
    cursor = 0
    while cursor + 2 < len(tokens):
        if tokens[cursor + 1].value != "=":
            cursor += 1
            continue
        start = cursor
        cursor += 2
        if tokens[cursor].value == "{":
            depth = 0
            while cursor < len(tokens):
                depth += tokens[cursor].value == "{"
                depth -= tokens[cursor].value == "}"
                cursor += 1
                if depth == 0:
                    break
            else:
                raise ValueError(f"Unterminated block near line {tokens[start].line}")
        else:
            cursor += 1
        result.append((tokens[start].value, tokens[start:cursor]))
    return result


def values(tokens: Iterable[Token]) -> list[str]:
    return [token.value for token in tokens]


class SourceTree:
    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[str, tuple[bytes, str, list[Token]]] = {}

    def read(self, relative_path: str) -> tuple[bytes, str, list[Token]]:
        if relative_path not in self.cache:
            payload = self.root.joinpath(relative_path).read_bytes()
            text = payload.decode("utf-8-sig")
            self.cache[relative_path] = payload, text, tokenize(text)
        return self.cache[relative_path]

    def definition(self, relative_path: str, key: str) -> dict[str, object]:
        payload, text, tokens = self.read(relative_path)
        matches = [body for name, body in assignments(tokens) if name == key]
        if len(matches) != 1:
            raise ValueError(f"Expected one definition {key} in {relative_path}, got {len(matches)}")
        body = matches[0]
        body_tokens = values(body)
        return {
            "relative_path": relative_path,
            "line": body[0].line,
            "end_line": body[-1].line,
            "file_sha256": sha256(payload),
            "block_sha256": sha256(text[body[0].offset:body[-1].end].encode("utf-8")),
            "ordered_token_sha256": sha256(canonical_bytes(body_tokens)),
            "token_count": len(body_tokens),
            "tokens": body_tokens,
            "token_objects": body,
        }


def portable_definition(definition: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in definition.items()
            if key not in {"tokens", "token_objects"}}


def token_diff(old: list[str], new: list[str]) -> list[dict[str, object]]:
    result = []
    matcher = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for kind, first, last, new_first, new_last in matcher.get_opcodes():
        if kind == "equal":
            continue
        result.append({
            "kind": kind, "old_token_range": [first, last],
            "new_token_range": [new_first, new_last],
            "old_tokens": old[first:last], "new_tokens": new[new_first:new_last],
            "old_context_before": old[max(0, first - 8):first],
            "old_context_after": old[last:last + 8],
            "new_context_before": new[max(0, new_first - 8):new_first],
            "new_context_after": new[new_last:new_last + 8],
        })
    return result


def section_comparison(old: dict[str, object], new: dict[str, object]) -> list[dict[str, object]]:
    old_fields = assignments(old["token_objects"][3:-1])  # type: ignore[index]
    new_fields = assignments(new["token_objects"][3:-1])  # type: ignore[index]
    old_counts: Counter[str] = Counter()
    new_counts: Counter[str] = Counter()
    def table(rows: list[tuple[str, list[Token]]], counts: Counter[str]):
        output = {}
        for name, tokens in rows:
            ordinal = counts[name]
            counts[name] += 1
            output[(name, ordinal)] = values(tokens)
        return output
    first = table(old_fields, old_counts)
    second = table(new_fields, new_counts)
    return [{"field": name, "ordinal": ordinal,
             "classification": ("unchanged-ordered-tokens" if first.get((name, ordinal)) == second.get((name, ordinal))
                                else "changed-ordered-tokens"),
             "token_differences": token_diff(first.get((name, ordinal), []), second.get((name, ordinal), []))}
            for name, ordinal in sorted(first.keys() | second.keys())]


def compare_block(old_tree: SourceTree, new_tree: SourceTree, path: str, key: str) -> dict[str, object]:
    old = old_tree.definition(path, key)
    new = new_tree.definition(path, key)
    return {"key": key,
            "classification": ("unchanged-ordered-tokens" if old["tokens"] == new["tokens"]
                               else "changed-ordered-tokens"),
            "old_definition": portable_definition(old), "new_definition": portable_definition(new),
            "token_differences": token_diff(old["tokens"], new["tokens"]),
            "fields": section_comparison(old, new) if len(old["tokens"]) >= 4 and old["tokens"][2] == "{" else []}


def epidemic_0110_dependencies(old_tree: SourceTree, new_tree: SourceTree) -> dict[str, object]:
    specs = [
        ("common/scripted_effects/06_dlc_ce1_epidemics_effects.txt", "plague_recovery_event_effect"),
        ("common/script_values/06_ce1_epidemics_values.txt", "epidemic_fromdust_value"),
        ("common/script_values/06_ce1_epidemics_values.txt", "former_infected_county_count"),
        ("common/script_values/00_legitimacy_values.txt", "miniscule_legitimacy_gain"),
        ("common/script_values/00_legitimacy_values.txt", "miniscule_legitimacy_loss"),
        ("common/scripted_effects/06_dlc_ce1_legitimacy_effects.txt", "add_legitimacy_effect"),
        ("common/scripted_triggers/06_ce1_legitimacy_triggers.txt", "is_valid_for_legitimacy_change"),
        ("common/script_values/01_dynamic_values.txt", "minor_gold_value"),
    ]
    specs.extend(("common/modifiers/06_ce1_modifiers.txt", key) for key in (
        "county_epidemic_recovered_strong_modifier", "county_epidemic_recovered_medium_modifier",
        "county_epidemic_recovered_minor_modifier", "county_epidemic_recovered_tiny_modifier", "plague_new_capital"))
    rows = {key: compare_block(old_tree, new_tree, path, key) for path, key in specs}
    epidemic_path = "common/epidemics/00_epidemics.txt"
    callers = {}
    for tree, build in ((old_tree, OLD_BUILD), (new_tree, NEW_BUILD)):
        payload, _, tokens = tree.read(epidemic_path)
        hooks = []
        for name, body in assignments(tokens):
            if len(body) < 4 or body[2].value != "{":
                continue
            for field, hook in assignments(body[3:-1]):
                if field == "on_province_recovered":
                    hook_values = values(hook)
                    if "plague_recovery_event_effect" in hook_values:
                        hooks.append({"epidemic_type": name, "line": hook[0].line,
                                      "tokens": hook_values,
                                      "ordered_token_sha256": sha256(canonical_bytes(hook_values))})
        callers[build] = {"relative_path": epidemic_path, "file_sha256": sha256(payload), "hooks": hooks}
    old_hooks = {row["epidemic_type"]: row["tokens"] for row in callers[OLD_BUILD]["hooks"]}
    new_hooks = {row["epidemic_type"]: row["tokens"] for row in callers[NEW_BUILD]["hooks"]}
    return {"scope": "direct-caller-recovery-hooks-and-listed-values-modifiers-only",
            "classification": "static-reviewed-narrow-dependencies",
            "full_transitive_dependency_graph_proven": False,
            "blocks": rows, "on_province_recovered_callers": callers,
            "recovery_hook_tokens_unchanged": old_hooks == new_hooks,
            "reviewed_semantics": {
                "native_option_2": "No treasury or gold cost; minor recovery (+2 development_growth) for major-or-worse epidemic, tiny recovery (+1 development_growth) otherwise, both five years; miniscule legitimacy loss when the scripted validity trigger permits it.",
                "miniscule_legitimacy_loss": -20,
                "legitimacy_condition": "has_legitimacy, alive, landed ruler, dynasty exists, county-or-higher, government neither theocracy nor republic. The old native2 used only has_legitimacy; the new eligibility is narrower.",
                "capital_selection_change": "The initial any_sub_realm_duchy candidate check excludes landless-type titles and uses optional title_capital_county ?= instead of mandatory title_capital_county =. The resulting new_preferred_capital remains optional.",
                "after": "Clears formerly_infected_counties variable list.",
                "scope": "epidemic required; new_preferred_capital optional.",
                "direct_caller": "Recovered county is recorded on county.holder.liege; epidemic records liege; each alive unflagged liege gets event after one day and a ten-day notification flag.",
            }}


def generate(old_root: Path, new_root: Path, source_index: Path,
             review_ledger: Path | None = None) -> dict[str, object]:
    frozen_payload = source_index.read_bytes()
    index = json.loads(frozen_payload.decode("utf-8"))
    old_tree, new_tree = SourceTree(old_root), SourceTree(new_root)
    events = {}
    counts: Counter[str] = Counter()
    for key, indexed in sorted(index["events"].items()):
        definition = indexed["definition"]
        if key in EXCLUDED:
            row = {"namespace": indexed["namespace"], "classification": "excluded-owner-boundary",
                   "reason": EXCLUDED[key], "old_definition": definition,
                   "status": "owner-deferred", "source_file_sha256": {},
                   "body_compared": False, "policy_reuse_eligible_by_body": False}
        else:
            path = definition["relative_path"]
            row = compare_block(old_tree, new_tree, path, key)
            if row["old_definition"]["file_sha256"] != definition["file_sha256"]:
                raise ValueError(f"Old source file no longer matches frozen index: {path}")
            dependencies = []
            for dep in sorted({candidate["relative_path"] for candidate in indexed["caller_candidates"]}):
                old_sha = sha256(old_tree.root.joinpath(dep).read_bytes())
                new_path = new_tree.root.joinpath(dep)
                new_sha = sha256(new_path.read_bytes()) if new_path.is_file() else None
                dependencies.append({"relative_path": dep, "old_file_sha256": old_sha,
                                     "new_file_sha256": new_sha,
                                     "file_bytes_unchanged": old_sha == new_sha,
                                     "call_edge_reviewed": False})
            row.update({"namespace": indexed["namespace"], "body_compared": True,
                        "status": "unchanged" if row["classification"] == "unchanged-ordered-tokens" else "changed",
                        "source_file_sha256": {path: row["new_definition"]["file_sha256"],
                                               **{dep["relative_path"]: dep["new_file_sha256"]
                                                  for dep in dependencies if dep["new_file_sha256"] is not None}},
                        "policy_reuse_eligible_by_body": row["classification"] == "unchanged-ordered-tokens",
                        "caller_candidate_files": dependencies,
                        "full_dependency_compatibility_proven": False})
        counts[row["classification"]] += 1
        events[key] = row
    narrow_review = epidemic_0110_dependencies(old_tree, new_tree)
    events["epidemic_events.0110"]["source_file_sha256"].update({
        row["new_definition"]["relative_path"]: row["new_definition"]["file_sha256"]
        for row in narrow_review["blocks"].values()})
    events["epidemic_events.0110"]["source_file_sha256"]["common/epidemics/00_epidemics.txt"] = narrow_review["on_province_recovered_callers"][NEW_BUILD]["file_sha256"]
    events["epidemic_events.0110"]["manual_review"] = {
        "status": "current-source-reviewed-bounded-continuation",
        "supported_selected_native_option_index": 2,
        "legacy_observed_native_option_tuple": [1, 2],
        "unobserved_new_build_projection": True,
        "policy_reuse_eligible_by_manual_review": True,
        "eligibility_scope": "Existing bounded continuation choosing native2; no affordability ranking or native0 capital-transfer projection claim.",
        "specific_changes": narrow_review["reviewed_semantics"],
        "narrow_dependency_reference": "epidemic_events_0110_narrow_dependency_review",
        "runtime_postcondition_proven": False,
    }
    events["epidemic_events.0110"]["policy_contract_compatible"] = True
    events["epidemic_events.0110"]["analysis_updates"] = {
        "option_semantics": {
            "2": narrow_review["reviewed_semantics"]["native_option_2"],
        },
        "legitimacy_condition": narrow_review["reviewed_semantics"]["legitimacy_condition"],
        "immediate_compatibility_change": narrow_review["reviewed_semantics"]["capital_selection_change"],
        "after_effect": narrow_review["reviewed_semantics"]["after"],
        "current_source_review_boundary": "Current source reviewed; no new-build paused projection or material postcondition claimed.",
    }
    review_sha256 = None
    if review_ledger is not None:
        review_payload = review_ledger.read_bytes()
        review_sha256 = sha256(review_payload)
        ledger = json.loads(review_payload.decode("utf-8"))
        for key, reviewed in ledger["events"].items():
            row = events[key]
            if (reviewed["old_ordered_token_sha256"] != row["old_definition"]["ordered_token_sha256"]
                    or reviewed["new_ordered_token_sha256"] != row["new_definition"]["ordered_token_sha256"]):
                raise ValueError(f"Reviewed event body changed: {key}")
            for field, value in reviewed.items():
                if field in {"old_ordered_token_sha256", "new_ordered_token_sha256"}:
                    continue
                if field in {"analysis_updates", "source_file_sha256"}:
                    row.setdefault(field, {}).update(value)
                else:
                    row[field] = value
    document = {
        "schema": "xar.ck3.nonwar-event-source-compatibility", "schema_version": 1,
        "old_ck3_build": index["ck3_build"], "old_ck3_exe_sha256": index["ck3_exe_sha256"],
        "ck3_build": NEW_BUILD, "ck3_exe_sha256": NEW_EXE_SHA256,
        "old_source_index_file_sha256": sha256(frozen_payload),
        "old_source_index_dataset_sha256": index["dataset_sha256"],
        "review_ledger_file_sha256": review_sha256,
        "token_comparison": "ordered tokens; whitespace/comments ignored; quoted text and escaping retained",
        "policy_reuse_boundary": "An unchanged reviewed body is eligible for static compatibility reuse only. Native runtime semantics, saved-scope projection, dependency graph and production OODA are not accepted by this comparison.",
        "live_acceptance_performed": False,
        "audit": {
            "registered_event_count": len(events), **dict(sorted(counts.items())),
            "current_bounded_continuation_source_compatible_count": sum(
                row["status"] == "unchanged" or row.get("policy_contract_compatible") is True
                for row in events.values()),
            "current_contract_adaptation_pending_count": sum(
                row["status"] == "changed" and row.get("policy_contract_compatible") is not True
                for row in events.values()),
        },
        "events": events,
        "epidemic_events_0110_narrow_dependency_review": narrow_review,
    }
    document["dataset_sha256"] = sha256(canonical_bytes(document))
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-game-root", type=Path, required=True)
    parser.add_argument("--new-game-root", type=Path, required=True)
    parser.add_argument("--source-index", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--review-ledger", type=Path)
    args = parser.parse_args()
    default_ledger = Path(__file__).resolve().parents[2].joinpath(
        "src/xar_autoplayer/vanilla_events/data/source_compatibility_reviews_1_20_0_2.json")
    review_ledger = args.review_ledger or (default_ledger if default_ledger.is_file() else None)
    document = generate(args.old_game_root, args.new_game_root, args.source_index, review_ledger)
    payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    if args.artifact_dir:
        args.artifact_dir.mkdir(parents=True, exist_ok=True)
        args.artifact_dir.joinpath(args.output.name).write_bytes(payload)
        args.artifact_dir.joinpath("source-compatibility-generation.json").write_text(
            json.dumps({"schema": "xar.ck3.nonwar-event-source-compatibility-generation",
                        "live_acceptance_performed": False,
                        "old_game_root": str(args.old_game_root), "new_game_root": str(args.new_game_root),
                        "generator_file_sha256": sha256(Path(__file__).read_bytes()),
                        "output_file_sha256": sha256(payload),
                        "dataset_sha256": document["dataset_sha256"],
                        "audit": document["audit"]}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit": document["audit"], "dataset_sha256": document["dataset_sha256"],
                      "output_file_sha256": sha256(payload)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
