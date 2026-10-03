"""External, acceptance-only structure/provenance check; never launches CK3 or Steam."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent
PACK = BASE / "mod_li_yu_dao_native_prototype"
SOURCE = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def syntax_check(text: str, path: Path) -> list[str]:
    errors: list[str] = []
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for n, char in enumerate(text):
        if char == "\n":
            comment = False
        if comment:
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                errors.append(f"{path}: unmatched close brace at byte {n}")
    if depth or quoted:
        errors.append(f"{path}: brace depth {depth}, unterminated string {quoted}")
    return errors


def main() -> None:
    # CK3 localization requires a UTF-8 BOM; normalize only the external fixture files.
    for path in PACK.glob("localization/*/*.yml"):
        raw = path.read_bytes()
        if not raw.startswith(b"\xef\xbb\xbf"):
            path.write_bytes(b"\xef\xbb\xbf" + raw)

    errors: list[str] = []
    payload: list[dict[str, object]] = []
    locs: dict[str, set[str]] = {}
    for path in sorted(PACK.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(PACK).as_posix()
        payload.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix in {".txt", ".mod"}:
            errors.extend(syntax_check(text, path))
        if path.suffix == ".yml":
            keys = re.findall(r"^ ([A-Za-z0-9_]+):\d+ ", text, flags=re.M)
            if len(keys) != len(set(keys)):
                errors.append(f"{path}: duplicate localization keys")
            locs[path.parent.name] = set(keys)
    if locs.get("english") != locs.get("simp_chinese"):
        errors.append("English/Chinese localization key sets differ")

    triggers = (PACK / "common/scripted_triggers/lyd_np_triggers.txt").read_text(encoding="utf-8")
    effects = (PACK / "common/scripted_effects/lyd_np_effects.txt").read_text(encoding="utf-8")
    decisions = (PACK / "common/decisions/lyd_np_decisions.txt").read_text(encoding="utf-8")
    events = (PACK / "events/lyd_np_events.txt").read_text(encoding="utf-8")
    required = {
        "player actor": "is_ai = no" in triggers,
        "join guard": "limit = { lyd_np_join_ready_trigger = yes }" in effects,
        "detach guard": "limit = { lyd_np_detach_ready_trigger = yes }" in effects,
        "explicit pair": '"divergence(root.faith.main_rite)" < 100' in triggers,
        "preserved anchor": "this != faith.main_rite" in triggers,
        "dynamic result": "save_scope_as = lyd_np_new_faith" in effects,
        "persistent dynamic reference": "name = lyd_np_latest_faith value = scope:lyd_np_new_faith" in effects,
        "five-year Rite timer": effects.count("name = lyd_np_transition_cooldown value = yes years = 5") == 2,
        "marked title cleanup": "has_variable = lyd_np_owned_head" in effects,
        "three rounds": "var:lyd_np_completed_cycles = 3 var:lyd_np_completed_joins = 3" in events,
        "delayed checks": all(key in events for key in ("LYD_NP_JOIN_D1_PASS", "LYD_NP_JOIN_D30_PASS", "LYD_NP_DETACH_D1_PASS", "LYD_NP_DETACH_D30_PASS")),
        "AI decision weights": decisions.count("ai_will_do = { base = 0 }") == 3,
        "no native on_action override": not (PACK / "common/on_action").exists(),
        "no global define changes": not (PACK / "common/defines").exists(),
        "no hidden content convergence": not re.search(r"\bchange_rite_divergence\s*=", effects),
    }
    errors.extend(f"contract failed: {key}" for key, ok in required.items() if not ok)
    sources = [
        "common/religion/faith_types/_faith_types.info",
        "common/religion/rite_types/_rite_types.info",
        "common/religion/religion_types/00_confucianism.txt",
        "common/religion/doctrine_types/20_doctrines.txt",
        "common/religion/tenet_types/00_tenet_types.txt",
        "common/scripted_effects/00_religion_effects.txt",
        "common/scripted_effects/pam_antipope_effects.txt",
        "common/scripted_effects/pam_effects.txt",
        "common/casus_belli_types/00_event_war.txt",
        "common/character_interactions/pam_interactions.txt",
        "common/on_action/religion_on_actions.txt",
        "events/dlc/fp3/fp3_struggle_events.txt",
        "events/courtier_guest_management_events/courtier_guest_management_events.txt",
    ]
    launcher = SOURCE / "launcher/launcher-settings.json"
    version = json.loads(launcher.read_text(encoding="utf-8-sig"))
    steam_manifest = SOURCE.parents[1] / "appmanifest_1158310.acf"
    manifest_text = steam_manifest.read_text(encoding="utf-8-sig")
    build_match = re.search(r'"buildid"\s+"(\d+)"', manifest_text)
    evidence = {
        "source_root": str(SOURCE),
        "launcher_version": version["version"],
        "raw_version": version["rawVersion"],
        "launcher_sha256": digest(launcher),
        "steam_buildid": build_match.group(1) if build_match else None,
        "steam_manifest_path": str(steam_manifest),
        "steam_manifest_sha256": digest(steam_manifest),
        "evidence_level": "static-confirmed source / unverified runtime candidate",
        "exe_read": False,
        "sources": [{"path": key, "sha256": digest(SOURCE / "game" / key)} for key in sources],
    }
    # Verify referenced native tenet IDs exist, without claiming full semantic validity.
    native_tenets = (SOURCE / "game/common/religion/tenet_types/00_tenet_types.txt").read_text(encoding="utf-8-sig")
    for key in ("tenet_benevolent_governance", "tenet_harmonious_society", "tenet_pursuit_of_knowledge"):
        if not re.search(rf"^{key}\s*=", native_tenets, flags=re.M):
            errors.append(f"native tenet missing: {key}")
    (BASE / "native-source-evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {"status": "GREEN" if not errors else "RED", "scope": "structure/localization/guard contracts only", "live_status": "NOT_RUN", "errors": errors, "contracts": required, "payload": payload}
    (BASE / "static-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"static_status": report["status"], "live_status": "NOT_RUN", "errors": errors, "payload_files": len(payload)}, ensure_ascii=False))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
