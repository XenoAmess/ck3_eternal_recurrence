"""Finite H1 public calls and checked JSON contracts; never create a HoF."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal, TypedDict

Arm = Literal["ordinary", "promote"]
Obj = dict[str, object]
DECISION = "create_hof_decision"
QUERY = "ck3_query_ingame_decision_item_v1"
SITES = "ck3_query_player_holy_site_v1"
RELIGION = "ck3_query_player_religion_context_v1"
GOVERNANCE = "ck3_query_player_rite_governance_v1"
DETAIL = "ck3_query_player_holy_site_decision_detail_v1"
COOLDOWN = "ck3_query_player_holy_site_decision_cooldown_v1"
PROMOTE = "ck3_confirm_holy_site_decision_v1"
CENSUS = "ck3_inspect_gui_window_tree_v1"
READS = frozenset({SITES, RELIGION, GOVERNANCE, DETAIL, COOLDOWN, CENSUS, QUERY,
                  "ck3_get_capabilities", "ck3_take_snapshot"})
PRESENT = frozenset({"ck3_open_ingame_decisions_v1", "ck3_select_ingame_decision_item_v1",
                     "ck3_open_holy_site_decision_v1"})
LIFECYCLE = frozenset({"ck3_query_normal_exit_context_v1", "ck3_request_normal_exit_v1",
                      "ck3_observe_normal_exit_v1"})
MAX_CALLS = 64
SCALE = 100000
HOF_QUEUE_SHA = "6d785a1e668b2b2f5e700e2d76496929fd6c977414dd4e43f54bb26c012075b9"
SAVE_SHA = "de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07"


class Pin(TypedDict):
    path: str
    bytes: int
    sha256: str


class Scene(TypedDict):
    played_character_id: int
    date_raw: int
    game_pid: int
    connection_generation: int
    native_revision: int
    episode_run_id: str | None


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def obj(value: object, reason: str = "JSON object") -> Obj:
    if not isinstance(value, dict) or any(type(k) is not str for k in value):
        raise ValueError(reason)
    return {k: v for k, v in value.items()}


def array(value: object, reason: str = "JSON array") -> list[object]:
    if not isinstance(value, list):
        raise ValueError(reason)
    return list(value)


def integer(value: object, low: int = 0, high: int = 2**32-2) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Exact bounded integer required")
    return value


def text(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("Nonempty string required")
    return value


def encode(value: object) -> str:
    # Equality is in the JSON type domain: True never equals 1 here.
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read(path: Path) -> Obj:
    require(path.is_file() and not path.is_symlink(), "Original regular JSON file required")
    loaded: object = json.loads(path.read_text(encoding="utf-8-sig"))
    return obj(loaded)


def pin(path: Path) -> Pin:
    require(path.is_file() and not path.is_symlink(), "Original regular source/receipt required")
    path = path.resolve()
    require(path.is_file() and not path.is_symlink(), "Original regular source/receipt required")
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def checked_pin(value: object) -> Pin:
    row = obj(value)
    require(set(row) == {"path", "bytes", "sha256"}, "Exact source pin required")
    ref: Pin = {"path": text(row["path"]), "bytes": integer(row["bytes"], 0, 2**53-1),
                "sha256": text(row["sha256"])}
    require(Path(ref["path"]).is_absolute() and encode(pin(Path(ref["path"]))) == encode(ref),
            "Original pinned source/receipt changed")
    return ref


def write_once(path: Path, value: object) -> None:
    import os
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=True, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def reject_existing_promotion(root: Path, scope: Obj) -> None:
    rows = list(root.glob("*.json"))
    require(len(rows) <= 128, "Retained once ledger exceeds finite inventory")
    for path in rows:
        require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 131072,
                "Unexpected retained intent object")
        previous = read(path)
        old = previous.get("scope")
        if isinstance(old, dict) and all(encode(old.get(k)) == encode(v) for k, v in scope.items()):
            raise ValueError("Existing original promotion intent blocks replay across date/run/PID/generation: " + str(path))


def retained_h2(value: object) -> Obj:
    row = obj(value)
    pair = (row.get("schema"), row.get("case"))
    require(pair in {
        ("faith-engine-e02-r19-spiritual-head-case-v1", "faith-engine-e02-r19-spiritual-head-v1"),
        ("faith-engine-e02-r19-hof-ghw-combined-case-v1", "faith-engine-e02-r19-hof-ghw-combined-v1")},
        "Original H2 contract identity required; no case aliasing")
    require(row.get("decision_key") == DECISION and obj(row.get("saved_input")).get("sha256") == SAVE_SHA,
            "Original H2 mother/decision identity changed")
    return row


def arm(value: object) -> Arm:
    if value == "ordinary" and type(value) is str:
        return "ordinary"
    if value == "promote" and type(value) is str:
        return "promote"
    raise ValueError("Only ordinary/promote H1 arm")


def vector(value: object, *, promotion: bool = False) -> list[int]:
    q = obj(value)
    fields = {"raw_scale", "resource_vector_raw", "native_affordable"}
    require(set(q) == fields | ({"costs_raw"} if promotion else set()), "Complete full10 quote required")
    require(integer(q["raw_scale"]) == SCALE and q["native_affordable"] is True,
            "Native quote scale/affordability differs")
    raw = [integer(n, -(2**63), 2**63-1) for n in array(q["resource_vector_raw"])]
    require(len(raw) == 10, "All ten native resource slots required")
    if promotion:
        require(encode(q["costs_raw"]) == encode(dict(zip(("gold", "prestige", "piety", "treasury"),
                    (raw[0], raw[1], raw[2], raw[6])))), "Native currency indexes changed")
    return raw


def membership(value: object, faith: int) -> dict[str, bool]:
    value = obj(value)
    require(value.get("available") is True and value.get("read_only") is True
            and integer(value.get("player_faith_id")) == faith, "Current Faith membership unavailable")
    ids = [integer(n) for n in array(value.get("current_faith_holy_site_ids"))]
    require(0 < len(ids) <= 64 and len(ids) == len(set(ids)), "Complete bounded Faith site IDs required")
    result: dict[str, bool] = {}
    for item in array(value.get("current_faith_sites")):
        site = obj(item)
        require(site.get("available") is True, "Site row unknown")
        key = str(integer(site.get("holy_site_id")))
        require(key not in result, "Duplicate site")
        matches = [obj(e) for e in array(site.get("associated_faiths"))
                   if integer(obj(e).get("faith_id")) == faith]
        require(len(matches) == 1, "Current Faith edge absent/ambiguous")
        edge = matches[0]
        grade = edge.get("eminent")
        require(edge.get("available") is True and edge.get("faith_lists_site") is True
                and type(grade) is bool, "Native membership grade unknown")
        if not isinstance(grade, bool):
            raise ValueError("Grade must be Boolean")
        result[key] = grade
    require(set(result) == set(map(str, ids)), "Native membership list is incomplete")
    return result


def validate_step(name: str, tool: str, args: Obj, branch: Arm, site: int,
                  *, claimed_promote: bool = False) -> Obj:
    require(name.startswith("h1-") and len(name) <= 100, "Finite unique H1 step ID required")
    require(tool in READS | PRESENT | {PROMOTE}, "H1 forbids HoF Confirm, day, save, raw and other actions")
    needed: set[str] = set()
    if tool in {QUERY, "ck3_select_ingame_decision_item_v1"}:
        needed = {"decision_key"}
        require(args.get("decision_key") == DECISION, "Only actual create_hof detail")
    elif tool in {DETAIL, PROMOTE, "ck3_open_holy_site_decision_v1"}:
        needed = {"action", "holy_site_id"}
        require(branch == "promote" and args.get("action") == "promote"
                and integer(args.get("holy_site_id")) == site, "Only finite target promotion")
    elif tool == COOLDOWN:
        needed = {"action"}
        require(branch == "promote" and args.get("action") == "promote", "Only actual promotion cooldown")
    elif tool == SITES:
        needed = {"holy_site_id"}
        require(integer(args.get("holy_site_id")) == site, "Selected site differs")
    elif tool == CENSUS:
        needed = {"window_kind"}
        require(args.get("window_kind") == "decisions", "Only current Decisions census")
    require(set(args) == needed, "Unexpected public H1 arguments")
    require(tool != PROMOTE or claimed_promote, "Durable original promotion intent required")
    return {"id": name, "tool": tool, "args": args, "fresh_revision": True,
            "continue_on_error": True, "timeout": 20}


class SemanticSource(TypedDict):
    bytes: int
    sha256: str


class HofNativeCohort(TypedDict):
    schema: Literal["faith-e02-h1-native-cohort-v1"]
    qualification: Pin
    native_compile_source_commit: str
    published_dll: Pin
    hof_stock_default_wire_packets: Pin
    semantic_source_rows: dict[str, SemanticSource]
    sdk90_semantic_origin: Pin
    sdk90_reexecuted: Literal[False]


# These bind the HoF mechanism whose original 30 bodies / 90 SDK paths passed.
# They are semantic inputs, never the current DLL/compile identity.
HOF_SEMANTIC_SOURCES: dict[str, SemanticSource] = {
    "include/xar_bridge/ck3_12004_holy_site_adoption_detail.hpp": {
        "bytes": 6278, "sha256": "e2f025728ceef370081c47e1ad97abdfb62aee73e28b28ea108234b819ca6da9"},
    "src/ck3_12004_holy_site_adoption_detail.cpp": {
        "bytes": 33693, "sha256": "006ea561be2e20b0d4d7efe94f49bf6403271e38491726c03cd8176e4dba0491"},
    "src/ck3_12004_holy_site_adoption_detail_json.cpp": {
        "bytes": 10177, "sha256": "8e56ac00ce0df1ef01845fa84c9b06a98db191106fb6efd4adb3fddbd95cf6ac"},
    "src/ck3_12004_holy_site_adoption_detail_test.cpp": {
        "bytes": 40920, "sha256": "1e9a892bc11bc774f591c74785873541029cc8771521a983b44df9a248c84e22"},
}
SDK90_ORIGIN_SHA = "39055f0626b3afc35c8b74db4c016dd24f0125eba5285687718d03109ae1de67"


def packet_identities(value: object) -> dict[str, SemanticSource]:
    index = obj(value)
    require(index.get("packet_kind") == "hof_stock_default"
            and index.get("owned_result_dtos") is True and index.get("game_queried") is False,
            "Actual owned HoF body index required; not live qualification")
    packets: dict[str, SemanticSource] = {}
    for value_ref in array(index.get("packets")):
        ref = checked_pin(value_ref)
        name = Path(ref["path"]).name
        require(name not in packets, "Duplicate native HoF packet name")
        packets[name] = {"bytes": ref["bytes"], "sha256": ref["sha256"]}
    require(len(packets) == 30, "Complete actual stock-default 30-body mechanism evidence required")
    return packets


def qualified_hof_cohort(value: object) -> HofNativeCohort:
    """Bind actual Native identity; inherit only unchanged, source-bound HoF facts."""
    ref = checked_pin(value)
    qualified = read(Path(ref["path"]))
    commit = text(qualified.get("source_commit"))
    require(len(commit) == 40 and all(c in "0123456789abcdef" for c in commit)
            and qualified.get("schema") == "ck3-qualified-native-build-v1"
            and qualified.get("machine_id") == "4-8e1c2f1861", "Actual qualified Native cohort required")
    dll = checked_pin(qualified.get("published_dll"))
    fresh_ref = checked_pin(qualified.get("hof_stock_default_wire_packets"))
    fresh = read(Path(fresh_ref["path"]))
    snapshot = read(Path(checked_pin(qualified.get("snapshot"))["path"]))
    require(snapshot.get("native_source_commit") == commit, "Native snapshot compile identity differs")
    actual: dict[str, SemanticSource] = {}
    for value_row in array(snapshot.get("files")):
        row = obj(value_row)
        relative = text(row.get("native_relative"))
        if relative in HOF_SEMANTIC_SOURCES:
            require(relative not in actual, "Duplicate HoF semantic source row")
            actual[relative] = {"bytes": integer(row.get("bytes"), 1, 2**53-1),
                                "sha256": text(row.get("sha256"))}
    require(encode(actual) == encode(HOF_SEMANTIC_SOURCES), "HoF mechanism changed; obtain new semantic qualification")
    # The retained source package and its original consumer remain immutable.
    origin = Path(ref["path"]).parents[2] / "qualifications/hof-sdk-native-seam-a01/run-a02/RESULT.actual.json"
    origin_ref = pin(origin)
    proof = read(origin)
    require(origin_ref["sha256"] == SDK90_ORIGIN_SHA and proof.get("result") == "PASS"
            and integer(proof.get("tests_run")) == 90 and integer(proof.get("skipped")) == 0
            and integer(proof.get("original_popen_wait_returncode")) == 0,
            "Retained original SDK90 semantic evidence required; no new run claimed")
    old_ref = checked_pin(proof.get("actual_wire_index"))
    old = read(Path(old_ref["path"]))
    require(encode(packet_identities(fresh)) == encode(packet_identities(old))
            and encode(checked_pin(fresh.get("executable"))) == encode(checked_pin(old.get("executable"))),
            "Fresh actual HoF bodies or fixture differ from the qualified semantic origin")
    execution = read(Path(checked_pin(fresh.get("execution"))["path"]))
    require(integer(execution.get("original_wait_returncode")) == 0
            and execution.get("stopped_reason") is None, "Fresh HoF fixture did not complete")
    return {"schema": "faith-e02-h1-native-cohort-v1", "qualification": ref,
            "native_compile_source_commit": commit, "published_dll": dll,
            "hof_stock_default_wire_packets": fresh_ref, "semantic_source_rows": actual,
            "sdk90_semantic_origin": origin_ref, "sdk90_reexecuted": False}


class HofPythonSourceSet(TypedDict):
    helper_sha256: str
    sdk_contract_sha256: str
    shared_contract_sha256: str | None


# Old actual SDK90 origin, and the explicitly tested shared-typing successor.
# Every member of one cohort must match; mixtures and arbitrary helpers reject.
HOF_PYTHON_SOURCE_SETS: tuple[HofPythonSourceSet, ...] = (
    {"helper_sha256": HOF_QUEUE_SHA,
     "sdk_contract_sha256": "d473b5d835feb5b520e1185b932fb84c5993c5079461f95786abaf9c0c7110f5",
     "shared_contract_sha256": None},
    {"helper_sha256": "ce438dee534ca2a1237061563105c60fab407433cac2f347adf829612a167b5e",
     "sdk_contract_sha256": "e4fa5f2659fb6e173620b8fcb1c5e6dcc6e43a0472f0234f77b439772eef65f3",
     "shared_contract_sha256": "c97f2959656c870e0d9f76712b6d09c158781d79926d7939a1258debb1d04b4f"},
)


def verified_hof_python_sources(helper_path: Path, sdk_source: Path | None = None) -> HofPythonSourceSet:
    """Check the exact same source cohort on both sides of the helper/SDK seam."""
    helper = pin(helper_path)
    source = sdk_source if sdk_source is not None else helper_path.resolve().parents[1] / "ck3_autonomous_player/src"
    sdk = pin(source / "xar_autoplayer/bridge/ingame_decision_item_contract.py")
    for cohort in HOF_PYTHON_SOURCE_SETS:
        if helper["sha256"] != cohort["helper_sha256"] or sdk["sha256"] != cohort["sdk_contract_sha256"]:
            continue
        shared_sha = cohort["shared_contract_sha256"]
        if shared_sha is not None:
            shared = pin(source / "xar_autoplayer/selected_decision_terms_v1.py")
            require(shared["sha256"] == shared_sha, "HoF shared typed contract differs from reviewed source")
        return cohort
    raise ValueError("Integrate one complete reviewed HoF Python source cohort; no mixed or arbitrary source set")
