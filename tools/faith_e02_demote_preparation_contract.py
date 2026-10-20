"""Finite public demotion preparation contracts; no HoF or promotion submission."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal, TypedDict

import faith_e02_h1_queue as Q

CASE = "faith-engine-e02-h1-demote-preparation-v1"
SCHEMA = "faith-e02-h1-demote-preparation-case-v1"
MACHINE = "4-8e1c2f1861"
ACTOR, FAITH, RITE, DATE = 31254, 103, 150, 53144328
DEMOTE_SITE, PROMOTE_SITE, MAX_CALLS = 0, 32, 64
WINDOW = "ck3_query_ingame_ui_window_v1"
OPEN_WINDOW = "ck3_open_holy_site_window_v1"
OPEN_DECISION = "ck3_open_holy_site_decision_v1"
CONFIRM = "ck3_confirm_holy_site_decision_v1"
SAVE = "ck3_save_checkpoint"
READS = frozenset({Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN, WINDOW,
                   "ck3_get_capabilities", "ck3_take_snapshot"})
PRESENT = frozenset({OPEN_WINDOW, OPEN_DECISION})
REQUIRED = READS | PRESENT | {CONFIRM, SAVE} | Q.LIFECYCLE
READONLY_OPT_IN = frozenset({Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN})
Action = Literal["demote", "promote"]
Mutation = Literal["demote", "save-checkpoint"]


class Terms(TypedDict):
    action: Action
    site_id: int
    capture_epoch: int
    selected_item_token: int
    native_resource_quote: object
    resource_vector_raw: list[int]
    requirements: str
    cost_description: str


class SavedInput(TypedDict):
    save: str
    bytes: int
    sha256: str
    player_id: int
    date_raw: int


def terms(value: object, action: Action, site: int) -> Terms:
    v = Q.obj(value)
    decision = "demote_holy_site_decision" if action == "demote" else "elevate_holy_site_decision"
    Q.require(v.get("available") is True and v.get("read_only") is True
              and v.get("detail_present") is True and v.get("root_present") is True
              and v.get("action_ready") is False and v.get("decision_confirm_invoked") is False
              and v.get("adoption_completed_observed") is False
              and v.get("action") == action and v.get("decision_key") == decision
              and v.get("requested_decision_key") == decision,
              "Actual selected decision definition unavailable")
    Q.require(Q.integer(v.get("detail_actor_id")) == Q.integer(v.get("current_actor_id")) == ACTOR
              and Q.integer(v.get("played_character_id")) == ACTOR
              and Q.integer(v.get("date_raw"), -(2**31), 2**31-1) == DATE
              and Q.integer(v.get("requested_holy_site_id")) == Q.integer(v.get("parameter_holy_site_id"))
                  == Q.integer(v.get("selected_holy_site_id")) == site
              and v.get("parameter_and_selection_match") is True,
              "Actual selected decision actor/site/date differs")
    for key in ("native_detail_context_verified", "normal_requirements_legality_observed",
                "normal_requirements_can_confirm", "native_can_confirm", "bypass_requirements_observed",
                "native_resource_quote_available", "native_requirements_description_available",
                "native_cost_description_available"):
        Q.require(v.get(key) is True, "Current ordinary decision guard unavailable: " + key)
    Q.require(Q.integer(v.get("bypass_requirements_raw"), 0, 255) == 0, "Bypass must be zero")
    raw = Q.vector(v.get("native_resource_quote"), promotion=True)
    # The preparation accepts the stock piety-only demotion, including a free action.
    if action == "demote":
        Q.require(all(n == 0 for i, n in enumerate(raw) if i != 2) and raw[2] >= 0,
                  "Demotion quote must be complete and piety-only")
    return {"action": action, "site_id": Q.integer(site),
            "capture_epoch": Q.integer(v.get("capture_epoch"), 1, 2**53-1),
            "selected_item_token": Q.integer(v.get("selected_item_token"), 0, 2**32-1),
            "native_resource_quote": v["native_resource_quote"], "resource_vector_raw": raw,
            "requirements": Q.text(v.get("native_requirements_description")),
            "cost_description": Q.text(v.get("native_cost_description"))}


def stable_terms(first: Terms, second: Terms) -> None:
    Q.require(second["capture_epoch"] > first["capture_epoch"], "Independent later native detail required")
    a: Q.Obj = {k: v for k, v in first.items() if k != "capture_epoch"}
    b: Q.Obj = {k: v for k, v in second.items() if k != "capture_epoch"}
    Q.require(Q.encode(a) == Q.encode(b), "Reviewed decision terms changed")


def cooldown(value: object, action: Action) -> Q.Obj:
    v = Q.obj(value)
    decision = "demote_holy_site_decision" if action == "demote" else "elevate_holy_site_decision"
    Q.require(v.get("available") is True and v.get("read_only") is True
              and v.get("action") == action and v.get("decision_key") == decision
              and Q.integer(v.get("played_character_id")) == ACTOR
              and Q.integer(v.get("date_raw"), -(2**31), 2**31-1) == DATE
              and Q.integer(v.get("capture_epoch"), 1, 2**53-1) > 0
              and v.get("native_decision_cooldown_observed") is True
              and Q.obj(v.get("native_decision_cooldown")).get("active") is False,
              "Actual current same-actor inactive decision cooldown required")
    return v


def membership_post(before: dict[str, bool], after: dict[str, bool]) -> None:
    Q.require(sum(before.values()) == 3 and before.get(str(DEMOTE_SITE)) is True
              and before.get(str(PROMOTE_SITE)) is False, "Original three-main-site baseline required")
    expected = dict(before)
    expected[str(DEMOTE_SITE)] = False
    Q.require(after == expected and sum(after.values()) == 2,
              "Only the selected main-to-ordinary relation may change; Nadjaf remains ordinary")


def step(name: str, tool: str, args: Q.Obj, *, consumed: bool = False) -> Q.Obj:
    Q.require(name.startswith("h1-preparation-") and len(name) < 100, "Finite original step identity required")
    Q.require(tool in READS | PRESENT | {CONFIRM, SAVE}, "Tool outside single preparation scene")
    expected: set[str] = set()
    if tool in {Q.DETAIL, OPEN_DECISION, CONFIRM}:
        expected = {"action", "holy_site_id"}
        action, site = args.get("action"), Q.integer(args.get("holy_site_id"))
        Q.require((action == "demote" and site == DEMOTE_SITE)
                  or (tool != CONFIRM and action == "promote" and site == PROMOTE_SITE),
                  "Only one selected demotion and a read-only target promotion precheck")
    elif tool in {Q.SITES, OPEN_WINDOW}:
        expected = {"holy_site_id"}
        Q.require(Q.integer(args.get("holy_site_id")) in {DEMOTE_SITE, PROMOTE_SITE}, "Unexpected selected site")
    elif tool == WINDOW:
        expected = {"window_kind"}
        Q.require(args.get("window_kind") == "holy_site", "Only holy-site presentation")
    elif tool == Q.COOLDOWN:
        expected = {"action"}
        Q.require(args.get("action") in {"demote", "promote"}, "Unexpected cooldown action")
    Q.require(set(args) == expected, "Unexpected public preparation arguments")
    Q.require(tool not in {CONFIRM, SAVE} or consumed, "Durable original intent required before mutation")
    return {"id": name, "tool": tool, "args": args, "fresh_revision": True,
            "continue_on_error": True, "timeout": 45 if tool == SAVE else 20}


def claim(root: Path, run_id: str, kind: Mutation, evidence: object) -> Q.Pin:
    Q.require(root.is_absolute() and root.is_dir() and not root.is_symlink(), "Retained original ledger required")
    scope: Q.Obj = {"machine_id": MACHINE, "saved_sha256": Q.SAVE_SHA,
                   "played_character_id": ACTOR, "action": kind,
                   "holy_site_id": DEMOTE_SITE}
    # No date/run/PID/generation can change a consumed action's stable scope.
    Q.reject_existing_promotion(root, scope)
    path = root / (hashlib.sha256(Q.encode(scope).encode()).hexdigest() + ".h1-preparation.intent.json")
    Q.write_once(path, {"schema": "faith-e02-h1-preparation-once-intent-v1", "scope": scope,
                       "run_id": Q.text(run_id), "evidence": evidence, "automatic_retry": False,
                       "unknown_must_never_replay": True})
    return Q.pin(path)


def materialized(value: object, save_dir: Path, original_mother: Path) -> SavedInput:
    v = Q.obj(value)
    checkpoint, material = Q.obj(v.get("checkpoint")), Q.obj(v.get("materialization"))
    Q.require(checkpoint.get("status") == "saved" and material.get("available") is True,
              "Native Save ACK is insufficient: actual checkpoint materialization required")
    Q.require(type(checkpoint.get("overwrite_confirmed")) is bool,
              "Actual checkpoint overwrite observation required")
    path = Path(Q.text(checkpoint.get("path")))
    Q.require(path.is_absolute() and path.resolve() == (save_dir / "xar_checkpoint.ck3").resolve()
              and path.resolve() != original_mother.resolve()
              and Path(Q.text(material.get("save_dir"))).resolve() == save_dir.resolve(),
              "Checkpoint must materialize inside this isolated profile, never over the original mother")
    ref = Q.pin(path)
    Q.require(ref["bytes"] == Q.integer(checkpoint.get("size"), 1, 2**53-1)
              and ref["sha256"] == Q.text(checkpoint.get("sha256"))
              and Q.integer(checkpoint.get("date_raw"), -(2**31), 2**31-1) == DATE,
              "Materialized checkpoint bytes/SHA/date do not match the original Native receipt")
    return {"save": ref["path"], "bytes": ref["bytes"], "sha256": ref["sha256"],
            "player_id": ACTOR, "date_raw": DATE}
