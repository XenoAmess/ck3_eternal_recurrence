"""Strict DTO for the current original appointment window; no desktop fallback."""
from __future__ import annotations
import copy

CAPABILITY = "game.command.query-current-title-appointment-v1"
STEP = "query-ingame-ui-window-v1"
EXE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"

def _integer(value: object, low: int, high: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError(f"{name} is outside its exact integer contract")
    return value

def validate_request(expected_revision: int, requested_title_id: int | None,
        candidate_offset: int, candidate_limit: int, breakdown_character_id: int | None) -> dict[str, int | str]:
    _integer(expected_revision, 0, 2**64-1, "expected_revision")
    fields: dict[str, int | str] = {"window_kind": "title_appointment", "subject_id": 0,
        "requested_title_id": 0 if requested_title_id is None else _integer(requested_title_id, 1, 2**32-2, "requested_title_id"),
        "candidate_offset": _integer(candidate_offset, 0, 4096, "candidate_offset"),
        "candidate_limit": _integer(candidate_limit, 1, 64, "candidate_limit"),
        "breakdown_character_id": 0 if breakdown_character_id is None else _integer(breakdown_character_id, 1, 2**32-2, "breakdown_character_id")}
    return fields

def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(f"appointment observation rejected: {detail}")

def _id(v: object, name: str) -> int:
    return _integer(v, 0, 2**32-2, name)

def _tree(node: object, budget: list[int], depth: int = 0) -> int:
    _require(isinstance(node, dict) and depth <= 8, "invalid score tree")
    assert isinstance(node, dict)
    budget[0] += 1
    _require(budget[0] <= 128, "score node budget exceeded")
    for name in ("text0", "text1", "text2"):
        text = node.get(name)
        _require(isinstance(text, str) and len(text.encode("utf-8")) <= 512 and "\0" not in text, "invalid native score string")
        budget[1] += len(text.encode("utf-8"))
    _require(budget[1] <= 12000, "score text budget exceeded")
    value = _integer(node.get("value_raw"), -2**63, 2**63-1, "score value")
    _integer(node.get("factor_raw"), -2**63, 2**63-1, "score factor")
    _integer(node.get("mode"), -2**31, 2**31-1, "score mode")
    _integer(node.get("flags"), 0, 255, "score flags")
    children = node.get("children")
    _require(isinstance(children, list), "missing score children")
    for child in children:
        _tree(child, budget, depth+1)
    return value

def normalize_result(raw: object, *, fields: dict[str, int | str], native_revision: int,
        date_raw: int, actor_id: int) -> dict[str, object]:
    _require(isinstance(raw, dict), "missing native packet")
    assert isinstance(raw, dict)
    for name, expected in {"schema": "ck3-ingame-ui-window-v1", "available": True, "accepted": True,
            "status": "observed", "window_kind": "title_appointment", "window_name": "title_appointment",
            "window_exists": True, "effective_visible": True, "enabled": True, "dispatch_invoked": False,
            "verification_pending": False, "paused": True, "native_revision": native_revision,
            "date_raw": date_raw, "played_character_id": actor_id, "application_owner_thread_verified": True,
            "gui_owner_binding_verified": True, "game_version": "1.20.0.4"}.items():
        _require(raw.get(name) == expected and type(raw.get(name)) is type(expected), f"wrong {name}")
    _require(str(raw.get("executable_sha256", "")).upper() == EXE_SHA256, "wrong executable")
    _integer(raw.get("pump_epoch"), 1, 2**64-1, "pump epoch")
    _integer(raw.get("thread_id"), 1, 2**32-1, "owner thread")
    v = raw.get("title_appointment")
    _require(isinstance(v, dict), "missing appointment DTO")
    assert isinstance(v, dict)
    _require(v.get("schema") == "ck3-current-title-appointment-v1" and v.get("available") is True, "unavailable current window")
    for name in ("requested_title_id", "candidate_offset", "breakdown_character_id"):
        _require(v.get(name) == fields[name], f"wrong requested {name}")
    current = _id(v.get("current_window_title_id"), "current title")
    holder = _id(v.get("current_holder_character_id"), "current holder")
    _require(raw.get("subject_id_available") is True and raw.get("current_subject_id") == current
        and raw.get("owner_character_id_available") is True and raw.get("owner_character_id") == holder, "wrapper title/holder mismatch")
    for name in ("current_title_key", "effective_succession_law_key"):
        s = v.get(name)
        _require(isinstance(s, str) and bool(s) and len(s) <= 160 and s.isascii()
            and all(c.isalnum() or c == "_" for c in s), f"invalid {name}")
    if fields["requested_title_id"]:
        _id(v.get("requested_holder_character_id"), "requested holder")
        resolved = _id(v.get("resolved_title_id"), "resolved title")
        _require(v.get("group_first_title_id") == resolved and v.get("native_group_branch") in {"character_1c0", "character_1d0"}, "normalization relationship unverified")
        _require(type(v.get("requested_resolves_to_current")) is bool and v["requested_resolves_to_current"] == (resolved == current), "wrong normalization equality")
        _require(isinstance(v.get("resolved_title_key"), str) and bool(v["resolved_title_key"]), "missing resolved key")
        if resolved == current:
            _require(v["resolved_title_key"] == v["current_title_key"] and v["requested_holder_character_id"] == holder, "normalized current scope mismatch")
    else:
        _require(v.get("requested_resolves_to_current") is False and v.get("resolved_title_id") == 0, "unrequested normalization")
    count = _integer(v.get("full_candidate_count"), 0, 4096, "full candidate count")
    _require(v.get("source_pool_count") == count and v.get("ai_control_available") is True
        and v.get("score_fixed_point_scale") == 100000
        and v.get("candidate_scope") == "complete_native_base_list_joined_to_source_pool_and_score_cache", "full pool provenance missing")
    offset = int(fields["candidate_offset"])
    end = min(count, offset+int(fields["candidate_limit"]))
    _require(offset <= count and v.get("next_offset") == end, "invalid page boundaries")
    token = v.get("pool_consistency_token")
    _require(isinstance(token, str) and token.startswith("fnv1a64:") and len(token) == 24
        and all(c in "0123456789abcdef" for c in token[8:]), "invalid pool consistency token")
    candidates = v.get("candidates")
    _require(isinstance(candidates, list) and len(candidates) == end-offset, "incomplete candidate page")
    ids, indices = set(), set()
    for c in candidates:
        _require(isinstance(c, dict), "invalid candidate")
        cid = _id(c.get("character_id"), "candidate full ID")
        index = _integer(c.get("list_index"), 0, count-1, "native list index")
        _require(cid not in ids and index not in indices, "duplicate candidate")
        ids.add(cid); indices.add(index)
        rank = _integer(c.get("native_rank"), -1, count, "native rank")
        _integer(c.get("score_raw"), -2**63, 2**63-1, "native fixed point score")
        for flag in ("alive", "is_human_player", "is_ai"):
            _require(type(c.get(flag)) is bool, f"unknown {flag}")
        _require(c["is_ai"] == (not c["alive"] or not c["is_human_player"])
            and c.get("score_present") is (rank > 0) and c.get("candidate_pool_member") is True, "AI/score provenance mismatch")
    _require(type(v.get("breakdown_available")) is bool and type(v.get("breakdown_getter_invoked")) is bool
        and v.get("breakdown_cache_refresh_only") is True, "invalid getter boundary")
    if v["breakdown_available"]:
        _require(bool(fields["breakdown_character_id"]) and v["breakdown_getter_invoked"] is True, "unrequested breakdown")
        total = _tree(v.get("breakdown"), [0, 0])
        matched = [c for c in candidates if c["character_id"] == fields["breakdown_character_id"]]
        if matched:
            _require(matched[0]["score_present"] is True and matched[0]["score_raw"] == total, "score breakdown total mismatch")
    else:
        _require(v.get("breakdown") is None, "unavailable breakdown has data")
    return copy.deepcopy(raw)
