"""Explicit external fixture startup policy and actual current-actor observations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from ..ck3_runtime_diagnostics import MAX_LITERAL_CHARS, MAX_LOG_LITERALS

ROBERT_KEY = "bookmark_rags_to_riches_duke_robert"
EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"


def require_fixture_frontend_build(capabilities: object) -> dict[str, int]:
    from .frontend_gui_route_contract import frontend_gui_route_binding_from_capabilities
    binding = frontend_gui_route_binding_from_capabilities(capabilities)
    rows = [capabilities]
    matches = []
    while rows:
        row = rows.pop()
        if not isinstance(row, dict):
            continue
        if isinstance(row.get("backends"), list):
            rows.extend(row["backends"])
        diagnostics = row.get("diagnostics")
        hello = diagnostics.get("hello") if isinstance(diagnostics, dict) else None
        if (isinstance(hello, dict) and hello.get("pid") == binding["bridge_pid"]
                and hello.get("connection_generation") == binding["connection_generation"]):
            matches.append(hello)
    if not matches or any((hello.get("game_adapter_id"), hello.get("expected_ck3_version"),
            hello.get("expected_ck3_sha256")) != ("ck3-1.20.0.3-msvc-x64", "1.20.0.3", EXE_SHA256)
            for hello in matches):
        raise ValueError("fixture frontend startup requires the actual exact .3 bridge")
    return binding


def require_fixture_selected_robert(selected: object) -> dict[str, object]:
    if not isinstance(selected, dict) or any(selected.get(key) != wanted for key, wanted in {
            "schema": "ck3-frontend-selected-1066-feudal-candidate-v1", "status": "ready", "read_only": True,
            "selected_bookmark_key": "bm_1066_rags_to_riches", "selected_character_name_key": ROBERT_KEY,
            "selected_character_government_key": "feudal_government"}.items()) or (
            selected.get("read_only") is not True) or (
            selected.get("selected_bookmark_group_key") not in {None, "bm_group_1066"}) or (
            type(selected.get("selected_bookmark_start_date_raw")) is not int):
        raise ValueError("fixture Start lacks an actual pre-Start Robert model receipt")
    return selected


def require_fixture_start_submission(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("fixture Start submission is not an object")
    for key, expected in {"schema": "ck3-frontend-fixture-robert-start-submission-v1", "schema_version": 1,
            "status": "acknowledged_verification_pending", "accepted": True, "pre_start_identity_proven": True,
            "postcondition_verified": False, "fixture_target_identity_proven": False,
            "requested_character_name_key": ROBERT_KEY, "uses_ocr": False,
            "uses_keyboard": False, "uses_mouse": False}.items():
        if type(value.get(key)) is not type(expected) or value[key] != expected:
            raise ValueError("fixture Start submission has an unadmitted " + key)
    require_fixture_selected_robert(value.get("selected_candidate"))
    ack = value.get("acknowledgement")
    if not isinstance(ack, dict) or ack.get("accepted") is not True or any(ack.get(key) != wanted for key, wanted in {
            "step": "activate-frontend-start-selected-bookmark-v1", "accepted": True,
            "status": "acknowledged_verification_pending", "backend_id": "native-headless"}.items()):
        raise ValueError("fixture Start ACK is malformed")
    binding = value.get("binding")
    if not isinstance(binding, dict) or set(binding) != {"bridge_pid", "connection_generation"} or any(
            type(binding[key]) is not int or binding[key] <= 0 for key in binding):
        raise ValueError("fixture Start lacks its actual process/connection binding")
    return value


def validate_fixture_start_policy(value: object) -> dict[str, object]:
    fields = {"schema", "schema_version", "preparation", "profile_input_sha256", "post_start",
              "required_log_markers", "forbidden_log_markers"}
    if not isinstance(value, dict) or set(value) != fields or value["schema"] != "ck3-frontend-fixture-start-policy-v1" or (
            type(value["schema_version"]) is not int or value["schema_version"] != 1):
        raise ValueError("unsupported closed fixture startup policy")
    preparation = value["preparation"]
    if not isinstance(preparation, dict) or set(preparation) != {"path", "sha256"} or (
            not isinstance(preparation["path"], str) or not Path(preparation["path"]).is_absolute()):
        raise ValueError("fixture policy must bind its exact external preparation")
    hashes = value["profile_input_sha256"]
    if not isinstance(hashes, dict) or not 3 <= len(hashes) <= 4096 or not {"dlc_load.json", "pdx_settings.txt"} <= set(hashes):
        raise ValueError("fixture policy must bind actual profile config and mounted inputs")
    for key, digest in {**hashes, "preparation": preparation["sha256"]}.items():
        if not isinstance(key, str) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("fixture input digest is malformed")
        if key != "preparation" and (Path(key).is_absolute() or ".." in Path(key).parts or "\\" in key or ":" in key):
            raise ValueError("fixture profile input must stay below the bound profile")
    post = value["post_start"]
    if not isinstance(post, dict) or set(post) != {"government_key", "primary_title_tier_key", "independent"} or (
            post["government_key"] not in {"feudal_government", "celestial_government"}) or (
            post["primary_title_tier_key"] not in {"empire", "hegemony"}) or post["independent"] is not True:
        raise ValueError("fixture policy requires explicit delivered government/tier/independence predicates")
    markers = []
    for name in ("required_log_markers", "forbidden_log_markers"):
        rows = value[name]
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_LOG_LITERALS or any(
                not isinstance(row, str) or not 1 <= len(row) <= MAX_LITERAL_CHARS or any(c in row for c in "\r\n\0") for row in rows):
            raise ValueError("fixture qualification markers are malformed")
        markers.extend(rows)
    if len(markers) > MAX_LOG_LITERALS:
        raise ValueError("fixture qualification exceeds the existing fixed log query limit")
    if len(markers) != len(set(markers)):
        raise ValueError("fixture qualification markers must be distinct")
    return json.loads(json.dumps(value))


def load_bound_fixture_start_policy(path: Path, profile_dir: Path) -> tuple[dict[str, object], bytes]:
    raw = path.resolve().read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError("fixture policy exceeds one MiB")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("fixture policy contains duplicate JSON fields")
            result[key] = value
        return result
    policy = validate_fixture_start_policy(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique))
    preparation = Path(policy["preparation"]["path"])
    if hashlib.sha256(preparation.read_bytes()).hexdigest() != policy["preparation"]["sha256"]:
        raise ValueError("fixture preparation bytes changed")
    profile = profile_dir.resolve()
    for relative, wanted in policy["profile_input_sha256"].items():
        source = (profile / relative).resolve()
        if not source.is_relative_to(profile) or not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != wanted:
            raise ValueError("fixture profile input bytes changed: " + relative)
    mounted = {p.relative_to(profile).as_posix() for top in ("mod", "mod-content")
               for p in (profile / top).rglob("*") if p.is_file()}
    declared = {key for key in policy["profile_input_sha256"] if key.startswith(("mod/", "mod-content/"))}
    if not mounted or mounted != declared:
        raise ValueError("fixture mounted input inventory changed")
    dlc = json.loads((profile / "dlc_load.json").read_text(encoding="utf-8-sig"))
    enabled = dlc.get("enabled_mods")
    if not isinstance(enabled, list) or not enabled or any(
            not isinstance(relative, str) or relative not in declared for relative in enabled):
        raise ValueError("fixture enabled mods are not bound mounted descriptors")
    # A cold, new profile is necessary to distinguish this run's qualification.
    if any(p.is_file() and p.stat().st_size for p in (profile / "logs").rglob("*")):
        raise ValueError("fixture startup requires fresh empty profile logs")
    return policy, raw


def fixture_business_context_binding(snapshot: object, root: object, policy: dict[str, object],
        submission: dict[str, object]) -> dict[str, object] | None:
    if not isinstance(snapshot, dict) or not isinstance(root, dict):
        raise ValueError("fixture current-actor observations must be objects")
    if snapshot.get("map_ready") is not True or snapshot.get("paused") is not True:
        return None
    if snapshot.get("episode_projection") != "native_campaign":
        raise ValueError("fixture observation would bind a one-life episode")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, dict) or any(diagnostics.get(key) != wanted for key, wanted in submission["binding"].items()):
        raise ValueError("fixture map crossed the admitted native frontend process")
    selected_date = submission["selected_candidate"]["selected_bookmark_start_date_raw"]
    if snapshot.get("date_raw") != selected_date:
        raise ValueError("fixture startup advanced away from the actual bookmark date")
    if root.get("campaign_root_context_ready") is not True:
        return None
    if root.get("backend_id") != "native-headless" or any(root.get(key) != snapshot.get(wanted) for key, wanted in {
            "queried_snapshot_id": "snapshot_id", "queried_revision": "revision", "queried_native_revision": "native_revision",
            "date_raw": "date_raw"}.items()):
        raise ValueError("fixture campaign-root observation is not bound to the actual paused frame")
    provenance = root.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("game_version") != "1.20.0.3" or str(
            provenance.get("executable_sha256")).upper() != EXE_SHA256:
        raise ValueError("fixture campaign root lacks exact .3 native provenance")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, dict) else None
    if type(actor) is not int or actor < 1 or root.get("player_character_id") != actor or root.get("player_character_alive") is not True:
        raise ValueError("fixture snapshot and native campaign root disagree on the actual living actor")
    government, title = root.get("government"), root.get("primary_title")
    wanted = policy["post_start"]
    if not isinstance(government, dict) or government.get("key") != wanted["government_key"] or (
            not isinstance(title, dict) or title.get("tier_key") != wanted["primary_title_tier_key"]) or root.get("independent") is not True:
        return None
    if type(title.get("title_id")) is not int or title["title_id"] < 1 or title.get("tier_raw") != {
            "empire": 5, "hegemony": 6}[wanted["primary_title_tier_key"]] or root.get("top_liege_character_id") != actor or (
            root.get("immediate_liege_character_id") is not None):
        raise ValueError("fixture actual primary-title/tier/liege identities are inconsistent")
    heartbeat = diagnostics.get("last_heartbeat")
    mailbox = heartbeat.get("main_thread_query_mailbox_v1") if isinstance(heartbeat, dict) else None
    epoch = mailbox.get("pump_epochs") if isinstance(mailbox, dict) else None
    if type(epoch) is not int or epoch < 0:
        raise ValueError("fixture business actor lacks an actual application-main pump epoch")
    return {"actor_character_id": actor, "primary_title_id": title["title_id"], "government_key": government["key"],
        "primary_title_tier_key": title["tier_key"], "date_raw": selected_date, **submission["binding"],
        "pump_epoch": epoch, "fixture_target_identity_proven": False}
