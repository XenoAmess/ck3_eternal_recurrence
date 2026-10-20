"""Two independent restores, one ordinary arm or one legal promotion; no HoF creation."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import os
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

import faith_e02_h1_queue as Q

CASE = "faith-engine-e02-h1-hof-quote-comparison-v1"
SCHEMA = "faith-e02-h1-quote-comparison-case-v1"
CLOSED = ("opt_in_holy_site_creation_ui", "opt_in_holy_site_creation_create_once",
          "opt_in_holy_site_relic_actions", "opt_in_player_rite_creation_actions",
          "opt_in_player_pilgrimage_execution", "opt_in_player_artifact_personal_use_actions",
          "opt_in_player_inventory_window_open", "opt_in_player_inventory_window_close")


class Client(Protocol):
    operator_reviewer: str
    manifest: Q.Obj
    def snapshot(self, *, require_event_free: bool = True) -> object: ...
    def execute_plan(self, steps: list[Q.Obj], name: str, timeout: float | None = None,
                     reserve: Literal[90] = 90) -> object: ...
    def guard(self, reserve: float = 0) -> object: ...
    def root_checkpoint(self, name: str, payload: Q.Obj, reserve: int = 120) -> object: ...


@runtime_checkable
class Quotes(Protocol):
    __file__: str
    def quote_terms(self, row: Q.Obj, actor: int, date_raw: int) -> object: ...
    def verify_quote_pair(self, claim: Q.Obj) -> object: ...


@runtime_checkable
class Opening(Protocol):
    __file__: str
    def opening_binding(self, frame: object) -> object: ...
    def actual_visible_decisions_tree(self, tree: object) -> bool: ...


@runtime_checkable
class Prepare(Protocol):
    def materialize_product_profile(self, context: Q.Obj, unused: None, configuration: object) -> object: ...
    def finish_product_profile(self, context: Q.Obj, profile: Q.Obj, *, provenance: Q.Obj) -> object: ...


def selected_quotes() -> Quotes:
    module: object = importlib.import_module("faith_e02_hof_queue")
    if not isinstance(module, Quotes):
        raise ValueError("Qualified public HoF quote helper unavailable")
    Q.verified_hof_python_sources(Path(module.__file__))
    return module


def selected_opening(context: Q.Obj) -> Opening:
    source = Path(Q.text(context.get("shared_source_root")))
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source /= "ck3_autonomous_player/src"
    module: object = importlib.import_module("xar_autoplayer.bridge.ingame_decisions_open_contract")
    if not isinstance(module, Opening):
        raise ValueError("Actual selected opening-frame reader unavailable")
    Q.require(Path(module.__file__).resolve() ==
              (source / "xar_autoplayer/bridge/ingame_decisions_open_contract.py").resolve(),
              "Opening reader escaped the selected shared source")
    Q.verified_hof_python_sources(Path(selected_quotes().__file__), source)
    return module


def scene(value: object, opening: Opening) -> Q.Scene:
    frame = Q.obj(value)
    Q.require(frame.get("active_event") is None and frame.get("pending_character_interaction") is None,
              "Real interruption confounds H1; retain it for the shared native event policy")
    row = Q.obj(opening.opening_binding(frame))
    episode = row.get("episode_run_id")
    Q.require(episode is None or type(episode) is str, "Native episode identity malformed")
    if episode is not None and not isinstance(episode, str):
        raise ValueError("Native episode identity malformed")
    return {"played_character_id": Q.integer(row.get("played_character_id"), 1),
            "date_raw": Q.integer(row.get("date_raw"), -(2**31), 2**31-1),
            "game_pid": Q.integer(row.get("game_pid"), 1),
            "connection_generation": Q.integer(row.get("connection_generation"), 1),
            "native_revision": Q.integer(row.get("native_revision"), 1, 2**53-1),
            "episode_run_id": episode}


def cohort(manifest: object, qualification: object) -> Q.HofNativeCohort:
    bound = Q.qualified_hof_cohort(qualification)
    selected = Q.obj(manifest)
    dll = Q.obj(Q.obj(selected.get("native")).get("dll"))
    Q.require(selected.get("native_compile_source_commit") == bound["native_compile_source_commit"]
              and Q.encode(Q.checked_pin(selected.get("native_input_identity_evidence"))) ==
                  Q.encode(bound["qualification"])
              and Q.text(dll.get("sha256")) == bound["published_dll"]["sha256"]
              and Q.integer(dll.get("bytes"), 1, 2**53-1) == bound["published_dll"]["bytes"],
              "Selected actual runtime must bind this qualified Native source and DLL")
    return bound


def validate_contract(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = Q.obj(context.get("case_contract"))
    branch = Q.arm(c.get("arm"))
    Q.require(c.get("schema") == SCHEMA and c.get("case") == context.get("case") == CASE
              and c.get("product") == context.get("product") == "faith-engine", "H1 case identity differs")
    saved = Q.obj(c.get("saved_input"))
    Q.require(set(saved) == {"save", "bytes", "sha256", "player_id", "date_raw"}
              and Q.integer(saved.get("bytes"), 1, 2**53-1) == 69030069
              and saved.get("sha256") == Q.SAVE_SHA
              and Q.integer(saved.get("player_id")) == 31254
              and Q.integer(saved.get("date_raw"), -(2**31), 2**31-1) == 53144328,
              "Both H1 arms must restore the same immutable retained R19 mother")
    Q.text(saved.get("save"))
    Q.require(c.get("machine_id") == "4-8e1c2f1861" and c.get("profile") ==
              {"enabled_mods": [], "product_files": []} and c.get("native_culture_observed") is False
              and c.get("culture_control") == "same_immutable_mother_no_culture_mutator"
              and Q.integer(c.get("max_public_calls"), 1) == Q.MAX_CALLS
              and c.get("create_hof_submissions") == 0 and type(c.get("create_hof_submissions")) is int,
              "Vanilla source-controlled culture and no HoF Confirm are mandatory")
    Q.require(Q.integer(c.get("holy_site_id")) == 32, "H1 uses only the retained ordinary Nadjaf32 association")
    ledger = Path(Q.text(c.get("once_ledger_root")))
    inputs = Q.obj(context.get("case_inputs"))
    Q.require(ledger.is_absolute() and ledger.is_dir() and not ledger.is_symlink()
              and inputs.get("once_ledger_root") == str(ledger),
              "Reuse the explicitly retained H2 ledger directory; never mint a new retry root")
    original_h2 = Q.retained_h2(Q.read(Path(Q.checked_pin(c.get("h2_case_contract"))["path"])))
    Q.require(original_h2.get("once_ledger_root") == str(ledger),
              "Original retained H2 contract must bind the same mother and ledger directory")
    Q.require(Q.text(c.get("prior_setup_disclosure")) == Q.text(original_h2.get("prior_setup_disclosure")),
              "Retain the original mechanism-experiment preparation disclosure")
    spec = Q.obj(context.get("case_spec"))
    initial_plan = Q.read(Path(Q.text(spec.get("initial_plan"))))
    Q.require(Q.encode(initial_plan) == Q.encode({"steps": [Q.validate_step(
        "h1-initial-capabilities", "ck3_get_capabilities", {}, branch, 32)]}),
        "Exactly one declared initial capability read, included in the call cap")
    required = Q.READS | Q.PRESENT | Q.LIFECYCLE | ({Q.PROMOTE} if branch == "promote" else set())
    actual = [Q.text(x) for x in Q.array(spec.get("required_mcp_tools"))]
    Q.require(len(actual) == len(set(actual)) and set(actual) == required
              and all(spec.get(k) is False for k in CLOSED), "Finite H1 tool/permission surface differs")
    Q.require(set(Q.text(x) for x in Q.array(spec.get("opt_in_read_only_mcp_tools"))) ==
              {Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN}, "Explicit readonly tool set differs")
    dependencies = [Q.checked_pin(d) for d in Q.array(c.get("dependencies"))]
    required_sources = {Path(__file__).resolve(), Path(Q.__file__).resolve(),
                        Path(selected_quotes().__file__).resolve()}
    Q.require(required_sources <= {Path(d["path"]).resolve() for d in dependencies},
              "Pin this adapter, finite queue and qualified HoF helper")
    manifest_ref = Q.checked_pin(context.get("runtime_manifest"))
    cohort(Q.read(Path(manifest_ref["path"])), c.get("native_qualification"))
    selected_quotes()
    return c


def prepare_case(context_value: object) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    saved = Q.obj(c["saved_input"])
    Q.require(Q.encode(context.get("saved_campaign")) == Q.encode(saved), "Prepare selected another mother")
    source = Path(Q.text(saved["save"]))
    before = source.stat()
    actual = Q.pin(source)
    Q.require(actual["bytes"] == saved["bytes"] and actual["sha256"] == saved["sha256"]
              and source.stat().st_mtime_ns == before.st_mtime_ns, "Immutable mother changed")
    inputs = Q.obj(context["case_inputs"])
    grant = Q.read(Path(Q.checked_pin(inputs.get("storage_admission"))["path"]))
    expiry = datetime.fromisoformat(Q.text(grant.get("expires_at_utc")).replace("Z", "+00:00"))
    Q.require(grant.get("active") is True and grant.get("machine_id") == c["machine_id"]
              and expiry.tzinfo is not None and datetime.now(timezone.utc) < expiry, "Fresh scene admission required")
    module: object = importlib.import_module("ck3_mod_acceptance_prepare")
    if not isinstance(module, Prepare):
        raise ValueError("Public preparation functions unavailable")
    profile = Q.obj(module.materialize_product_profile(context, None, inputs.get("configuration")))
    profile = Q.obj(module.finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": "H1-independent-" + Q.arm(c["arm"]),
        "saved_input": saved, "fresh_restore_observed": False, "preparation_mod_mounted": False,
        "h2_case_contract": c["h2_case_contract"], "prior_setup_disclosure": c["prior_setup_disclosure"],
        "native_culture_observed": False, "culture_control": c["culture_control"]}))
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
            "saved_campaign": {**saved, "product_inventory": Q.obj(profile["product_inventory"])["path"]}},
            "profile": profile, "initial_plan": Q.obj(context["case_spec"])["initial_plan"],
            "runtime_status": "NOT_RUN", "business_pass": False}


def wallet(value: object) -> dict[str, int]:
    frame = Q.obj(value)
    result: dict[str, int] = {}
    for name in ("gold", "prestige", "piety"):
        coin = Q.obj(frame.get("played_character_" + name))
        Q.require(set(coin) == {"raw", "scale"} and Q.integer(coin["scale"]) == Q.SCALE,
                  "Actual signed public wallet/scale missing")
        result[name] = Q.integer(coin["raw"], -(2**63), 2**63-1)
    return result


def identity(religion: object, governance: object) -> Q.Obj:
    r, g = Q.obj(religion), Q.obj(governance)
    h = Q.obj(g.get("heads"))
    Q.require(r.get("available") is True and g.get("frame_available") is True and h.get("available") is True,
              "Fresh religion and governance/head components required")
    for value, fields in ((r, ("played_character_id", "faith_id", "rite_id", "faith_main_rite_id")),
                          (h, ("played_character_id", "faith_id", "actor_rite_id", "faith_main_rite_id"))):
        Q.require([Q.integer(value.get(k)) for k in fields] == [31254, 103, 150, 150],
                  "Actual actor/Faith/Rite/main Rite changed")
    Q.require(h.get("faith_religious_head_holder_character_id") is None,
              "Existing HoF is not an H1 creation-quote scene; never recreate or remove it")
    return {"actor": 31254, "faith": 103, "rite": 150, "faith_main_rite": 150,
            "head_holder": None, "native_culture_observed": False,
            "culture_control": "same_immutable_mother_no_culture_mutator"}


def hof_terms(row_value: object) -> Q.Obj:
    row = Q.obj(row_value)
    value = Q.obj(row.get("result"))
    Q.require(Q.integer(value.get("matching_row_count")) == 1, "Actual HOF row absent/ambiguous")
    for key in ("detail_actor_reference_key", "played_character_id"):
        Q.require(Q.integer(value.get(key)) == 31254, "Actual HoF actor is not the retained player")
    Q.require(Q.integer(value.get("date_raw"), -(2**31), 2**31-1) == 53144328, "HoF date changed")
    t = Q.obj(value.get("selected_terms"))
    Q.require(Q.integer(t.get("played_character_id")) == 31254
              and Q.integer(t.get("date_raw"), -(2**31), 2**31-1) == 53144328, "Terms actor/date malformed")
    # The public decision-item envelope has no capture_epoch; the typed
    # selected terms carry the independently captured native epoch.
    Q.integer(t.get("capture_epoch"), 1, 2**53-1)
    Q.integer(t.get("named_parameter_count"), 0, 1)
    Q.vector(t.get("resource_quote"))
    return Q.obj(selected_quotes().quote_terms(row, 31254, 53144328))


class ArmRun:
    def __init__(self, context: Q.Obj, client: Client, c: Q.Obj, opening: Opening) -> None:
        self.context, self.client, self.c, self.opening = context, client, c, opening
        self.branch, self.site = Q.arm(c["arm"]), Q.integer(c["holy_site_id"])
        self.output = Path(Q.text(context.get("output")))
        self.run_id = Q.text(context.get("run_id"))
        self.calls, self.number = 1, 0  # Includes the one declared initial public capability call.
        self.baseline: Q.Scene | None = None
        self.last_revision = 0
        self.attempted = False
        self.unknown = False
        self.intent: Q.Pin | None = None
        self.receipts: list[Q.Pin] = []

    def frame(self, value: object) -> Q.Obj:
        frame = Q.obj(value)
        current = scene(frame, self.opening)
        Q.require(current["played_character_id"] == 31254 and current["date_raw"] == 53144328,
                  "Actual restore differs from the retained mother actor/date")
        if self.baseline is None:
            self.baseline = current
        else:
            current_fields, original_fields = Q.obj(current), Q.obj(self.baseline)
            for key in ("played_character_id", "date_raw", "game_pid", "connection_generation", "episode_run_id"):
                Q.require(Q.encode(current_fields[key]) == Q.encode(original_fields[key]), "Arm crossed original scene: " + key)
        Q.require(current["native_revision"] >= self.last_revision, "Native revision regressed")
        self.last_revision = current["native_revision"]
        return frame

    def guard(self, count: int) -> None:
        Q.require(self.calls + count <= Q.MAX_CALLS, "H1 finite public call cap exhausted")
        self.client.guard(120 + 300 + count * 20 + 20)

    def snapshot(self) -> Q.Obj:
        self.guard(1)
        self.calls += 1
        return self.frame(self.client.snapshot(require_event_free=False))

    def call(self, tool: str, args: Q.Obj | None = None, *, claimed: bool = False) -> Q.Obj:
        self.guard(2 if tool not in Q.READS else 1)
        if tool not in Q.READS:
            self.snapshot()  # Actual host only promises after_snapshot; never invent before_snapshot.
        self.number += 1
        name = "h1-" + self.branch + "-" + str(self.number).zfill(3)
        step = Q.validate_step(name, tool, args or {}, self.branch, self.site, claimed_promote=claimed)
        self.calls += 1
        rows = Q.array(self.client.execute_plan([step], name, timeout=20, reserve=90))
        Q.require(len(rows) == 1, "One original public row required")
        row = Q.obj(rows[0])
        if "before_snapshot" in row:
            self.frame(row["before_snapshot"])
        self.frame(row.get("after_snapshot"))
        self.receipts.append(Q.pin(self.output / (name + ".actual-results.json")))
        Q.require(row.get("ok") is True and not row.get("error"), "Actual public call rejected: " + tool)
        value = Q.obj(row.get("result"))
        if "played_character_id" in value:
            Q.require(Q.integer(value["played_character_id"]) == 31254
                      and Q.integer(value.get("date_raw"), -(2**31), 2**31-1) == 53144328,
                      "Native result crossed actual actor/date")
        return row

    def result(self, tool: str, args: Q.Obj | None = None, *, claimed: bool = False) -> Q.Obj:
        return Q.obj(self.call(tool, args, claimed=claimed)["result"])

    def sites(self) -> dict[str, bool]:
        return Q.membership(self.result(Q.SITES, {"holy_site_id": self.site}), 103)

    def heads(self) -> Q.Obj:
        return identity(self.result(Q.RELIGION), self.result(Q.GOVERNANCE))

    def terms(self, row: object) -> Q.Obj:
        return hof_terms(row)

    def quote_pair(self) -> Q.Obj:
        census = self.result(Q.CENSUS, {"window_kind": "decisions"})
        if not self.opening.actual_visible_decisions_tree(census):
            self.result("ck3_open_ingame_decisions_v1")
            Q.require(self.opening.actual_visible_decisions_tree(
                self.result(Q.CENSUS, {"window_kind": "decisions"})), "Actual Decisions not visible")
        keyed = self.result(Q.QUERY, {"decision_key": Q.DECISION})
        Q.require(keyed.get("available") is True and Q.integer(keyed.get("matching_row_count")) == 1,
                  "Actual HoF row is absent or ambiguous")
        self.result("ck3_select_ingame_decision_item_v1", {"decision_key": Q.DECISION})
        refs: list[Q.Pin] = []
        terms: list[Q.Obj] = []
        epochs: list[int] = []
        for _ in range(2):
            self.snapshot()
            row = self.call(Q.QUERY, {"decision_key": Q.DECISION})
            terms.append(self.terms(row))
            epochs.append(Q.integer(terms[-1].get("capture_epoch"), 1, 2**53-1))
            refs.append(self.receipts[-1])
        Q.require(epochs[1] > epochs[0], "HoF quotes need independent increasing native capture epochs")
        claim: Q.Obj = {"schema": "faith-e02-R19-hof-once-claim-v1", "decision_key": Q.DECISION,
                        "actor": 31254, "date_raw": 53144328, "quote_receipts": refs}
        selected_quotes().verify_quote_pair(claim)  # Pure consumer, not a persisted H2 intent.
        for key in ("resource_quote", "requirements_description", "cost_description", "context_adapter",
                    "named_parameter_count", "stock_default_parameter"):
            Q.require(Q.encode(terms[0].get(key)) == Q.encode(terms[1].get(key)), "Two actual quote terms changed")
        return {"quote_receipts": refs, "capture_epochs": epochs, "terms": terms,
                "resource_vector_raw": Q.vector(terms[0]["resource_quote"]), "raw_scale": Q.SCALE,
                "script_validity_observed_by_native_CanConfirm": True, "hof_confirm_submissions": 0}


def promotion_terms(value: object, site: int) -> Q.Obj:
    v = Q.obj(value)
    Q.require(v.get("available") is True and v.get("read_only") is True and v.get("action") == "promote"
              and v.get("decision_key") == v.get("requested_decision_key") == "elevate_holy_site_decision"
              and Q.integer(v.get("detail_actor_id")) == Q.integer(v.get("current_actor_id")) == 31254
              and Q.integer(v.get("parameter_holy_site_id")) == Q.integer(v.get("selected_holy_site_id")) == site
              and v.get("parameter_and_selection_match") is True, "Actual selected promotion identity unavailable")
    for key in ("native_detail_context_verified", "normal_requirements_legality_observed",
                "normal_requirements_can_confirm", "native_can_confirm", "bypass_requirements_observed",
                "native_resource_quote_available", "native_requirements_description_available",
                "native_cost_description_available"):
        Q.require(v.get(key) is True, "Actual ordinary promotion guard unavailable: " + key)
    Q.require(Q.integer(v.get("bypass_requirements_raw"), 0, 255) == 0, "No bypass")
    raw = Q.vector(v.get("native_resource_quote"), promotion=True)
    # This public wallet exposes three balances. Do not invent seven unseen debits.
    Q.require(all(n == 0 for n in raw[3:]) and all(n >= 0 for n in raw[:3]),
              "This finite promotion requires all non-public-wallet quoted costs zero")
    return {"native_resource_quote": v["native_resource_quote"],
            "resource_vector_raw": raw, "selected_item_token": Q.integer(v.get("selected_item_token"), 0, 2**32-1),
            "requirements": Q.text(v.get("native_requirements_description")),
            "cost_description": Q.text(v.get("native_cost_description"))}


def promote_once(run: ArmRun, before_sites: dict[str, bool]) -> Q.Obj:
    target: Q.Obj = {"action": "promote", "holy_site_id": run.site}
    run.result("ck3_open_holy_site_decision_v1", target)
    first = promotion_terms(run.result(Q.DETAIL, target), run.site)
    cooldown = run.result(Q.COOLDOWN, {"action": "promote"})
    observation: Q.Obj = {"site_id": run.site, "terms": first, "cooldown": cooldown,
                          "membership_before": before_sites, "create_hof_submissions": 0}
    review = Q.obj(run.client.root_checkpoint("h1-promote-original-quote-review", observation, reserve=120))
    Q.require(review.get("run_id") == run.run_id and review.get("reviewer") == run.client.operator_reviewer
              and review.get("status") == "complete" and review.get("original_image_directly_reviewed") is True
              and review.get("promote_once_authorized") is True
              and review.get("reviewed_native_observation_sha256") == hashlib.sha256(Q.encode(observation).encode()).hexdigest(),
              "Actual Root review of this quote and one legal promotion required")
    image = Q.checked_pin(review.get("original_image"))
    Q.require(Path(image["path"]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "Original PNG review required")
    before = run.snapshot()
    second = promotion_terms(run.result(Q.DETAIL, target), run.site)
    Q.require(Q.encode(first) == Q.encode(second) and run.sites() == before_sites, "Promotion terms/grades changed")
    root = Path(Q.text(run.c["once_ledger_root"]))
    scope: Q.Obj = {"machine_id": run.c["machine_id"], "saved_sha256": Q.SAVE_SHA,
                   "played_character_id": 31254, "action": "promote", "holy_site_id": run.site}
    intent = root / (hashlib.sha256(Q.encode(scope).encode()).hexdigest() + ".h1-promote.intent.json")
    run.guard(8)
    run.unknown = True  # A retained matching intent is never reset by a fresh restore.
    Q.reject_existing_promotion(root, scope)
    Q.write_once(intent, {"schema": "faith-e02-h1-promote-once-intent-v1", "scope": scope,
                         "run_id": run.run_id, "scene": run.baseline, "review": review, "terms": second,
                         "unknown_must_never_replay": True})
    run.attempted, run.unknown = True, True
    run.intent = Q.pin(intent)
    ack = run.call(Q.PROMOTE, target, claimed=True)
    after_sites = run.sites()
    after = run.snapshot()
    expected = dict(before_sites)
    Q.require(expected.get(str(run.site)) is False, "Target was not an ordinary Faith member")
    expected[str(run.site)] = True
    old_wallet, new_wallet = wallet(before), wallet(after)
    debit = {name: old_wallet[name] - new_wallet[name] for name in old_wallet}
    raw = [Q.integer(n, -(2**63), 2**63-1) for n in Q.array(second["resource_vector_raw"])]
    Q.require(after_sites == expected and list(debit.values()) == raw[:3],
              "Independent exact promotion grade and actual wallet debit not proven; never replay")
    run.unknown = False
    proof: Q.Obj = {"intent": Q.pin(intent), "ack": ack, "before": before, "after": after,
                   "membership_before": before_sites, "membership_after": after_sites,
                   "full10_quote": second["native_resource_quote"], "actual_wallet_debit_raw": debit,
                   "payment_total_proven": True, "independent_promotion_observed": True}
    Q.write_once(run.output / "h1-promote-independent-post.json", proof)
    return proof


def run_case(context_value: object, client: Client) -> Q.Obj:
    context = Q.obj(context_value)
    c = validate_contract(context)
    native_cohort = cohort(client.manifest, c["native_qualification"])
    run = ArmRun(context, client, c, selected_opening(context))
    allocation = Q.pin(Path(Q.text(context.get("run_dir"))) / "allocated-context.json")
    allocated = Q.read(Path(allocation["path"]))
    Q.require(allocated.get("schema") == "ck3-mod-acceptance-run-context-v1"
              and allocated.get("run_id") == run.run_id and allocated.get("case") == CASE,
              "Actual separately allocated H1 run identity required")
    result: Q.Obj = {"schema": "faith-e02-h1-arm-result-v1", "machine_id": c["machine_id"],
        "run_id": run.run_id, "arm": run.branch, "holy_site_id": run.site,
        "mother_sha256": Q.SAVE_SHA, "once_ledger_root": c["once_ledger_root"],
        "native_qualification": native_cohort["qualification"],
        "native_compile_source_commit": native_cohort["native_compile_source_commit"],
        "native_cohort": native_cohort,
        "native_culture_observed": False, "culture_control": c["culture_control"],
        "prior_setup_disclosure": c["prior_setup_disclosure"],
        "allocated_context": allocation,
        "public_calls_include_declared_initial_capability_read": True,
        "status": "PARTIAL", "hof_confirm_submissions": 0, "business_pass": False}
    try:
        initial = run.snapshot()
        result["scene"] = run.baseline
        result["identity_before"] = run.heads()
        initial_sites = run.sites()
        Q.require(initial_sites.get(str(run.site)) is False, "Both arms must begin with the selected ordinary site")
        result["membership_before"] = initial_sites
        result["wallet_initial"] = wallet(initial)
        if run.branch == "promote":
            result["promotion"] = promote_once(run, initial_sites)
        result["hof_quotes"] = run.quote_pair()
        final_sites = run.sites()
        expected_sites = dict(initial_sites)
        if run.branch == "promote":
            expected_sites[str(run.site)] = True
        Q.require(final_sites == expected_sites, "Faith membership changed outside the one intended promotion")
        result["membership_final"] = final_sites
        result["faith_membership_counts"] = {"ordinary": sum(not x for x in final_sites.values()),
                                              "eminent": sum(final_sites.values())}
        result["counts_are_realm_controlled_qualifying_counts"] = False
        result["identity_after"] = run.heads()
        result["final_snapshot"] = run.snapshot()
        expected_wallet = wallet(initial) if run.branch == "ordinary" else wallet(
            Q.obj(result["promotion"])["after"])
        Q.require(wallet(result["final_snapshot"]) == expected_wallet, "Wallet changed outside the one intended promotion")
        result["status"] = "QUOTED_NO_HOF_SUBMISSION"
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
    result.update(public_calls=run.calls, promotion_attempts=int(run.attempted),
                  promotion_outcome_unknown=run.unknown, promotion_intent=run.intent, receipts=run.receipts)
    Q.write_once(run.output / "h1-arm-result.json", result)
    return result


def verify_case(context_value: object) -> Q.Obj:
    """Validate this completed arm through the existing strict quote consumer."""
    context = Q.obj(context_value)
    c = validate_contract(context)
    # The join imports this adapter's pure term readers; defer that import until
    # the public loader has finished loading the adapter.
    from faith_e02_h1_join import checked_arm
    ref = Q.pin(Path(Q.text(context.get("output"))) / "h1-arm-result.json")
    result = checked_arm(ref, Q.arm(c["arm"]))
    Q.require(result.get("run_id") == context.get("run_id")
              and result.get("machine_id") == c["machine_id"]
              and Q.integer(result.get("holy_site_id")) == Q.integer(c["holy_site_id"]),
              "Actual H1 result belongs to another public run")
    return {"status": result["status"], "arm": result["arm"], "h1_quoted": True,
            "hof_confirm_submissions": 0, "arm_result": ref,
            "business_pass": False, "business_contract_applicable": False,
            "case_contract_qualified": False, "gui_contract_qualified": False,
            "whole_product_acceptance_credit": False, "product_release_pass": False,
            "automatic_retry": False}
