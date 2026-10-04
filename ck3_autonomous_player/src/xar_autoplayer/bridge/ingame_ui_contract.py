"""Four explicit native presentation routes; no planner/desktop fallback."""
from __future__ import annotations
import math
import hashlib
import re
from collections.abc import Mapping
from .public_unit_contract import public_cunit_id
from .version_identity import CK3_11906, CK3_12003, NativeBuildIdentity, require_exact_native_build

NAVIGATE_STEP = "navigate-ingame-ui-v1"
QUERY_STEP = "query-ingame-ui-window-v1"
NAVIGATE_CAPABILITY = "game.command.navigate-ingame-ui-v1"
QUERY_CAPABILITY = "game.command.query-ingame-ui-window-v1"
KINDS = {"character", "army", "combat", "knights"}
OPERATIONS = {"open_character": "character", "select_army": "army", "open_combat": "combat", "open_knights": "knights",
              "hover_left_knights":"combat", "hover_right_knights":"combat", "fit_combat_window":"combat",
              "hover_army_tooltip":"army", "leave_army_tooltip":"army"}
ARMY_TOOLTIP_KINDS = {"supply_state", "attrition"}


def validate_ui_request(operation: str, kind: str, subject_id: int, revision: int, *,
                        army_tooltip_kind: str | None = None,
                        army_tooltip_receipt: str | None = None) -> None:
    if kind not in KINDS or (operation != "query" and OPERATIONS.get(operation) != kind):
        raise ValueError("unsupported typed UI operation/window")
    if isinstance(revision, bool) or not isinstance(revision, int) or not 0 <= revision < 2**64:
        raise ValueError("expected_revision must be uint64")
    if isinstance(subject_id, bool) or not isinstance(subject_id, int):
        raise ValueError("subject ID must be a full uint32 handle")
    if army_tooltip_kind is not None:
        if (not isinstance(army_tooltip_kind, str) or army_tooltip_kind not in ARMY_TOOLTIP_KINDS
                or kind != "army" or operation not in {"query", "hover_army_tooltip", "leave_army_tooltip"}):
            raise ValueError("unsupported army tooltip operation/kind")
        public_cunit_id(subject_id, "subject public CUnitID")
        if operation == "hover_army_tooltip":
            if army_tooltip_receipt is not None:
                raise ValueError("initial army tooltip hover has no caller receipt")
        elif not isinstance(army_tooltip_receipt, str) or re.fullmatch(r"[0-9a-f]{32}", army_tooltip_receipt) is None:
            raise ValueError("army tooltip requires a 32 lower-case hex action receipt")
        return
    if army_tooltip_receipt is not None or operation in {"hover_army_tooltip", "leave_army_tooltip"}:
        raise ValueError("army tooltip operation/receipt requires its semantic kind")
    if operation in {"query", "open_knights"}:
        if subject_id != 0:
            raise ValueError("this operation has no caller-selected subject")
    elif operation == "select_army":
        public_cunit_id(subject_id, "subject public CUnitID")
    elif not 0 < subject_id < 2**32 - 1:
        raise ValueError("subject ID must be positive and exclude the invalid handle")


def ingame_ui_build_binding(snapshot: Mapping[str, object]) -> tuple[NativeBuildIdentity, bool]:
    """Bind UI reads to hello; archived inputs without hello remain legacy only."""
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(diagnostics, Mapping) or "hello" not in diagnostics:
        return CK3_11906, False
    hello = diagnostics["hello"]
    if not isinstance(hello, Mapping):
        raise ValueError("native UI exact-build hello is malformed")
    build = require_exact_native_build(
        hello.get("expected_ck3_version", hello.get("game_version")),
        hello.get("expected_ck3_sha256", hello.get("executable_sha256")),
    )
    if build not in (CK3_11906, CK3_12003):
        raise ValueError("native UI exact build has no migrated presentation route")
    # A hello with both field spellings must not contradict its selected pair.
    if "game_version" in hello and hello["game_version"] != build.game_version:
        raise ValueError("native UI hello version mirror differs")
    if "executable_sha256" in hello:
        mirror = hello["executable_sha256"]
        if not isinstance(mirror, str) or mirror.upper() != build.executable_sha256:
            raise ValueError("native UI hello executable mirror differs")
    return build, True


def validate_ui_build_scope(build: NativeBuildIdentity, operation: str, kind: str, *,
                            army_tooltip_kind: str | None = None) -> None:
    if build not in (CK3_11906, CK3_12003):
        raise ValueError("native UI exact build has no migrated presentation route")
    if army_tooltip_kind is not None:
        if build != CK3_12003 or kind != "army" or operation not in {"query", "hover_army_tooltip", "leave_army_tooltip"}:
            raise ValueError("army tooltips require the exact current native Army route")
        return
    if build == CK3_12003 and (kind != "army" or operation not in {"query", "select_army"}):
        raise ValueError("current native UI supports army query and select only")


def normalize_ui_result(value: object, *, operation: str, kind: str, subject_id: int,
                         native_revision: int, date_raw: int, actor_id: int,
                         expected_build: NativeBuildIdentity = CK3_11906,
                         army_tooltip_kind: str | None = None,
                         army_tooltip_receipt: str | None = None) -> dict[str, object]:
    validate_ui_build_scope(expected_build, operation, kind, army_tooltip_kind=army_tooltip_kind)
    if army_tooltip_kind is not None:
        validate_ui_request(operation, kind, subject_id, native_revision,
            army_tooltip_kind=army_tooltip_kind, army_tooltip_receipt=army_tooltip_receipt)
    if not isinstance(value, dict) or value.get("schema") != "ck3-ingame-ui-window-v1":
        raise ValueError("native UI result schema unavailable")
    expected = {"window_kind": kind, "requested_subject_id": subject_id, "native_revision": native_revision,
                "date_raw": date_raw, "paused": True, "played_character_id": actor_id}
    for key, target in expected.items():
        actual = value.get(key)
        if type(actual) is not type(target) or actual != target:
            raise ValueError(f"native UI binding mismatch: {key}")
    for key in ("accepted", "available", "dispatch_invoked", "verification_pending", "window_exists",
                "effective_visible", "enabled", "subject_id_available", "application_owner_thread_verified",
                "gui_owner_binding_verified"):
        if type(value.get(key)) is not bool:
            raise ValueError(f"native UI boolean missing: {key}")
    if expected_build == CK3_12003:
        owner_available = value.get("owner_character_id_available")
        if type(owner_available) is not bool or "owner_character_id" not in value:
            raise ValueError("current native UI owner availability/value missing")
        owner = value["owner_character_id"]
        if owner_available:
            # The native selected Unit owner is read as int32. Zero is an
            # actual ID when available; never infer it from a default value.
            if (not value["subject_id_available"] or isinstance(owner, bool)
                    or not isinstance(owner, int) or not 0 <= owner <= 2**31 - 1):
                raise ValueError("current native UI selected owner identity invalid")
        elif owner is not None:
            raise ValueError("unavailable current native UI owner must be explicit null")
    for key in ("current_subject_id", "native_army_id", "owner_character_id", "thread_id", "pump_epoch"):
        if expected_build == CK3_12003 and key == "owner_character_id":
            continue
        n = value.get(key)
        # Missing subject evidence can be explicit null; public CUnit zero is
        # still a valid selected ID when the availability flag is true.
        if (expected_build == CK3_12003 and key in {"current_subject_id", "native_army_id"}
                and key in value and n is None and not value["subject_id_available"]):
            continue
        if isinstance(n, bool) or not isinstance(n, int) or n < 0 or (key != "pump_epoch" and n >= 2**32):
            raise ValueError(f"native UI typed integer missing: {key}")
    if kind == "army" and value["subject_id_available"]:
        public_cunit_id(value["current_subject_id"], "current public CUnitID")
    if value["available"] != value["accepted"]:
        raise ValueError("native UI availability/acceptance differs")
    if value.get("rng_owner_is_ui_admission_gate") is not False:
        raise ValueError("native UI must use original application/GUI ownership rather than RNG ownership")
    for key,limit in (("gui_context_address",2**64),("gui_owner_address",2**64),("rng_owner_thread_id",2**32)):
        n=value.get(key)
        if isinstance(n,bool) or not isinstance(n,int) or not 0<=n<limit:
            raise ValueError(f"native UI owner diagnostic missing: {key}")
    unopened_current_select_ack = (
        expected_build == CK3_12003 and operation == "select_army" and kind == "army"
        and value["available"] and not value["window_exists"]
        and value.get("status") == "acknowledged_verification_pending"
        and value["dispatch_invoked"] and value["verification_pending"]
        and not value["effective_visible"] and not value["subject_id_available"]
    )
    if value["available"]:
        if (not value["application_owner_thread_verified"] or not value["gui_owner_binding_verified"] or
                not value["gui_context_address"] or not value["gui_owner_address"]):
            raise ValueError("native UI original application/GUI binding unverified")
        if not value["thread_id"] or not value["pump_epoch"] or (not value["window_exists"] and not unopened_current_select_ack):
            raise ValueError("native UI lacks owner/target-window observation")
        if operation == "query":
            expected_pending = army_tooltip_kind is not None
            if value.get("status") != "observed" or value["dispatch_invoked"] or value["verification_pending"] != expected_pending:
                raise ValueError("query result must be independent and read only")
        elif not value["verification_pending"] or value.get("status") not in {
            "acknowledged_verification_pending", "already_visible_verification_pending", "already_layout_fitted_verification_pending"
        }:
            raise ValueError("open ACK cannot claim a completed postcondition")
        if value.get("status")=="already_layout_fitted_verification_pending" and operation!="fit_combat_window":
            raise ValueError("layout-fit status belongs only to the explicit fit action")
        if kind == "knights" and (not value["subject_id_available"] or value["owner_character_id"] != actor_id
                                  or value["current_subject_id"] != actor_id):
            raise ValueError("knights UI owner is not the played actor")
    elif value.get("status") != "unavailable" or not isinstance(value.get("unavailable_reason"), str) or not value["unavailable_reason"]:
        raise ValueError("unavailable native UI needs an explicit reason")
    tree = value.get("tree")
    if not isinstance(tree, dict) or type(tree.get("truncated")) is not bool or type(tree.get("root_available")) is not bool:
        raise ValueError("native target-window census missing")
    count, widgets = tree.get("widget_count"), tree.get("widgets")
    census_limit = 2048 if expected_build == CK3_12003 else 512
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= census_limit or not isinstance(widgets, list) or len(widgets) != count:
        raise ValueError("native census count/bound mismatch")
    if expected_build == CK3_12003 and value.get("window_name") != "army_window":
        raise ValueError("current native UI window name is not the army window")
    if unopened_current_select_ack:
        if tree["root_available"] or count or tree["truncated"] or tree.get("scope_root_name") != "army_window":
            raise ValueError("unopened army ACK must keep an empty target-window census")
    elif value["available"] and (not tree["root_available"] or count < 1 or tree.get("scope_root_name") != value.get("window_name")):
        raise ValueError("native census is not scoped to the target window")
    for widget in widgets:
        if (not isinstance(widget,dict) or not isinstance(widget.get("runtime_name"),str) or not isinstance(widget.get("child_path"),str) or
                type(widget.get("effective_visible")) is not bool or type(widget.get("enabled")) is not bool):
            raise ValueError("native census widget fields malformed")
        for key in ("depth","child_count","vtable_rva"):
            n=widget.get(key)
            if isinstance(n,bool) or not isinstance(n,int) or n<0:
                raise ValueError("native census widget integer malformed")
    if value["available"] and not unopened_current_select_ack and (widgets[0]["runtime_name"]!=value["window_name"] or widgets[0]["depth"]!=0 or
                               widgets[0]["effective_visible"]!=value["effective_visible"]):
        raise ValueError("native census root differs from target-window observation")
    if value.get("knights_list_scope") != "military_eligible_not_active_combat_roster":
        raise ValueError("native knights list scope missing")
    observed_build = require_exact_native_build(value.get("game_version"), value.get("executable_sha256"))
    if observed_build != expected_build or value.get("native_backend_id") != expected_build.backend_id("ingame-ui-v1"):
        raise ValueError("native UI exact-build source binding missing")
    if type(value.get("combat_knights_read_available")) is not bool or value.get("combat_roster_full_ids_available") is not False:
        raise ValueError("native combat tooltip scope missing")
    for key in ("left_knight_breakdown","right_knight_breakdown","hovered_widget_name","hovered_ui_side"):
        if not isinstance(value.get(key), str):
            raise ValueError(f"native UI string missing: {key}")
    if type(value.get("hover_state_available")) is not bool or value.get("hover_readback_is_pixels") is not False:
        raise ValueError("hover observation must not claim pixels")
    hovered = value.get("hovered_combat_id")
    if isinstance(hovered, bool) or not isinstance(hovered,int) or not 0 <= hovered < 2**32:
        raise ValueError("hover CombatID unavailable")
    if value["hovered_widget_name"]:
        side=value["hovered_ui_side"]
        if (kind!="combat" or operation!="query" or not value["hover_state_available"] or not value["effective_visible"] or
                not value["subject_id_available"] or hovered!=value["current_subject_id"] or side not in {"left","right"} or
                value["hovered_widget_name"]!=side+"_knights"):
            raise ValueError("hover target is not bound to current visible CombatID")
    elif value["hovered_ui_side"] or hovered:
        raise ValueError("hover identity cannot be invented without fixed widget")
    for key in ("left_knight_count","right_knight_count"):
        n=value.get(key)
        if isinstance(n,bool) or not isinstance(n,int) or not -1<=n<=4096:
            raise ValueError("combat knight count type/bound invalid")
    if value["combat_knights_read_available"]:
        if kind!="combat" or operation!="query" or not value["effective_visible"] or not value["subject_id_available"] or min(value["left_knight_count"],value["right_knight_count"])<0:
            raise ValueError("tooltip getters require current visible full CombatID")
    elif (value["left_knight_count"]!=-1 or value["right_knight_count"]!=-1 or value["left_knight_breakdown"] or value["right_knight_breakdown"]):
        raise ValueError("unavailable tooltip must not retain readable numbers/text")
    normalize_combat_geometry(value,operation=operation,kind=kind)
    normalize_army_tooltip_result(value, operation=operation, subject_id=subject_id,
        tooltip_kind=army_tooltip_kind, action_receipt=army_tooltip_receipt)
    return dict(value)


def normalize_army_tooltip_result(value: dict[str, object], *, operation: str,
                                  subject_id: int, tooltip_kind: str | None,
                                  action_receipt: str | None) -> None:
    tooltip = value.get("army_tooltip")
    if tooltip_kind is None:
        if tooltip is not None:
            raise ValueError("unsolicited army tooltip observations")
        return
    fields = {"schema", "semantic_kind", "receipt_id", "action_owner_epoch", "later_owner_epoch",
        "cache_bytes_observed", "source_bound", "hover_matches_source", "active_stack_read", "active_count",
        "active_top_index", "active_top_locked", "active_root_available", "source_child_path",
        "tooltip_text_child_path", "leave_observed", "status", "unavailable_reason", "verification_pending",
        "gui_update_epoch", "text_refresh_verified", "rendered_verified", "available", "observed_cache"}
    if not isinstance(tooltip, dict) or not fields.issubset(tooltip):
        raise ValueError("army tooltip complete observation contract missing")
    if tooltip["schema"] != "ck3-army-tooltip-v1" or tooltip["semantic_kind"] != tooltip_kind:
        raise ValueError("army tooltip semantic kind/schema differs")
    for key in ("cache_bytes_observed", "source_bound", "hover_matches_source", "active_stack_read",
                "active_root_available", "leave_observed", "verification_pending", "available",
                "text_refresh_verified", "rendered_verified"):
        if type(tooltip[key]) is not bool:
            raise ValueError(f"army tooltip boolean missing: {key}")
    if (tooltip["available"] or tooltip["text_refresh_verified"] or tooltip["rendered_verified"]
            or tooltip["gui_update_epoch"] is not None):
        raise ValueError("army tooltip cache cannot claim GUI refresh or rendered success")
    if not isinstance(tooltip["unavailable_reason"], str):
        raise ValueError("army tooltip unavailable reason missing")
    nullable = ("receipt_id", "action_owner_epoch", "later_owner_epoch", "active_count", "active_top_index",
        "active_top_locked", "source_child_path", "tooltip_text_child_path", "observed_cache")
    evidence_flags = ("cache_bytes_observed", "source_bound", "hover_matches_source", "active_stack_read",
        "active_root_available", "leave_observed")
    if tooltip["status"] == "unavailable":
        if (not tooltip["unavailable_reason"] or tooltip["verification_pending"]
                or any(tooltip[key] is not None for key in nullable)
                or any(tooltip[key] for key in evidence_flags)):
            raise ValueError("unavailable army tooltip must clear all observations and receipt")
        return
    statuses = {"acknowledged_verification_pending", "cache_observed_verification_pending", "leave_observed_verification_pending"}
    if tooltip["status"] not in statuses or not tooltip["verification_pending"] or not value["available"]:
        raise ValueError("army tooltip evidence must remain verification pending")
    if operation != "query" and not value["dispatch_invoked"]:
        raise ValueError("army tooltip successful ACK lacks original dispatch")
    if (not value["window_exists"] or not value["effective_visible"] or not value["subject_id_available"]
            or value["current_subject_id"] != subject_id or value["tree"]["truncated"]):
        raise ValueError("army tooltip is not bound to the requested visible full Army ID")
    receipt = tooltip["receipt_id"]
    if not isinstance(receipt, str) or re.fullmatch(r"[0-9a-f]{32}", receipt) is None:
        raise ValueError("army tooltip native receipt malformed")
    if operation == "query" and receipt != action_receipt:
        raise ValueError("army tooltip query receipt differs from the requested action")
    epoch = tooltip["action_owner_epoch"]
    later = tooltip["later_owner_epoch"]
    if isinstance(epoch, bool) or not isinstance(epoch, int) or not 0 < epoch < 2**64:
        raise ValueError("army tooltip action owner epoch missing")
    if later is not None and (isinstance(later, bool) or not isinstance(later, int) or not epoch <= later < 2**64):
        raise ValueError("army tooltip later application owner epoch invalid")
    if operation == "query" and (later is None or later <= epoch):
        raise ValueError("army tooltip query requires a later application owner epoch")
    for key in ("source_child_path", "tooltip_text_child_path"):
        path = tooltip[key]
        if path is not None and (not isinstance(path, str) or (path and any(
                re.fullmatch(r"0|[1-9][0-9]*", part) is None for part in path.split("/")))):
            raise ValueError("army tooltip internal child path malformed")
    if not tooltip["source_bound"] or tooltip["source_child_path"] is None:
        raise ValueError("army tooltip source is not independently bound")
    count, index, locked = tooltip["active_count"], tooltip["active_top_index"], tooltip["active_top_locked"]
    if not tooltip["active_stack_read"]:
        if count is not None or index is not None or locked is not None or tooltip["active_root_available"]:
            raise ValueError("unread army tooltip stack must keep nullable observations")
    else:
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count < 2**31:
            raise ValueError("army tooltip actual stack count missing")
        if index is not None and (isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < count):
            raise ValueError("army tooltip active top index outside actual stack")
        if locked is not None and type(locked) is not bool:
            raise ValueError("army tooltip active lock observation malformed")
        if tooltip["active_root_available"] and (index is None or locked is None):
            raise ValueError("army tooltip active root lacks a top entry")
    cache = tooltip["observed_cache"]
    if tooltip["cache_bytes_observed"]:
        if (operation != "query" or tooltip["status"] != "cache_observed_verification_pending"
                or not tooltip["hover_matches_source"] or not tooltip["active_stack_read"]
                or not tooltip["active_root_available"] or locked is not False
                or tooltip["tooltip_text_child_path"] is None or tooltip["leave_observed"]):
            raise ValueError("army tooltip cache evidence lacks its actual bound active source")
        if not isinstance(cache, dict) or set(cache) != {"text", "utf8_bytes", "sha256"} or not isinstance(cache["text"], str):
            raise ValueError("army tooltip observed cache must contain actual complete text bytes")
        raw = cache["text"].encode("utf-8")
        size, digest = cache["utf8_bytes"], cache["sha256"]
        if (isinstance(size, bool) or not isinstance(size, int) or size != len(raw)
                or not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None
                or digest.lower() != hashlib.sha256(raw).hexdigest()):
            raise ValueError("army tooltip observed UTF8 size/SHA differs from complete text")
    elif cache is not None or tooltip["tooltip_text_child_path"] is not None:
        raise ValueError("unobserved army tooltip cache must remain explicit null")
    if tooltip["status"] == "cache_observed_verification_pending" and not tooltip["cache_bytes_observed"]:
        raise ValueError("army tooltip cache status needs actual cache byte evidence")
    if tooltip["status"] == "leave_observed_verification_pending":
        if operation != "query" or not tooltip["leave_observed"] or tooltip["hover_matches_source"] or not tooltip["active_stack_read"]:
            raise ValueError("army tooltip leave observation lacks an independent later query")
    elif tooltip["leave_observed"]:
        raise ValueError("army tooltip leave evidence must keep its pending leave status")
    if operation != "query" and tooltip["status"] != "acknowledged_verification_pending":
        raise ValueError("army tooltip action ACK cannot claim a completed observation")


def normalize_combat_geometry(value: dict[str, object], *, operation: str, kind: str) -> None:
    g=value.get("combat_geometry")
    if not isinstance(g,dict):
        raise ValueError("combat native geometry contract missing")
    for key in ("available","stock_margin_source_verified","content_inside_viewport","fit_required"):
        if type(g.get(key)) is not bool:
            raise ValueError(f"combat geometry boolean missing: {key}")
    if (g.get("coordinate_space")!="native_gui_absolute" or
            g.get("scope")!="visible_widget_union_and_verified_stock_background_margins" or
            g.get("readback_is_pixels") is not False or g.get("full_panel_pixels_proven") is not False):
        raise ValueError("native geometry cannot claim full panel pixels")
    for key in ("combat_id","widget_count"):
        n=g.get(key)
        if isinstance(n,bool) or not isinstance(n,int) or not 0<=n<(2**32 if key=="combat_id" else 513):
            raise ValueError("geometry typed identity/count invalid")
    def number(x: object) -> float:
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>1048576:
            raise ValueError("geometry finite numeric value required")
        return float(x)
    rects={}
    for key in ("viewport","window_rect","content_union"):
        r=g.get(key)
        if not isinstance(r,dict) or set(r)!={"x","y","width","height"}:
            raise ValueError("native geometry rectangle missing")
        rects[key]={k:number(x) for k,x in r.items()}
    delta=g.get("proposed_translation")
    if not isinstance(delta,dict) or set(delta)!={"x","y"}:
        raise ValueError("native geometry translation missing")
    dx,dy=number(delta["x"]),number(delta["y"])
    if not isinstance(g.get("unavailable_reason"),str) or not isinstance(g.get("stock_margin_source_sha256"),str):
        raise ValueError("geometry provenance/reason missing")
    stock="7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236"
    if g["stock_margin_source_sha256"]!=(stock if g["stock_margin_source_verified"] else ""):
        raise ValueError("stock background-margin source hash mismatch")
    if not g["available"]:
        if (not g["unavailable_reason"] or g["content_inside_viewport"] or g["fit_required"] or dx or dy or
                any(n for r in rects.values() for n in r.values())):
            raise ValueError("unavailable geometry must not retain a fit assertion or coordinates")
        return
    if (not value["available"] or kind!="combat" or operation not in {"query","fit_combat_window"} or
            not value["effective_visible"] or not value["subject_id_available"] or
            g["combat_id"]!=value["current_subject_id"] or not g["combat_id"] or
            not 1<=g["widget_count"]<=value["tree"]["widget_count"] or value["tree"]["truncated"] or
            not g["stock_margin_source_verified"] or g["unavailable_reason"]):
        raise ValueError("geometry is not a complete bound observation of the current visible CombatID")
    v,c=rects["viewport"],rects["content_union"]
    if any(r["width"]<=0 or r["height"]<=0 for r in rects.values()) or v["x"] or v["y"] or max(v["width"],v["height"])>65536:
        raise ValueError("native viewport/rectangle bounds invalid")
    tolerance=0.01
    if c["width"]>v["width"]+tolerance or c["height"]>v["height"]+tolerance:
        raise ValueError("oversized content cannot claim an admitted translation fit")
    for axis,size,d in (("x","width",dx),("y","height",dy)):
        expected=v[axis]-c[axis] if c[axis]<v[axis] else min(0.0,v[axis]+v[size]-c[axis]-c[size])
        if abs(d-expected)>tolerance:
            raise ValueError("geometry translation is not the minimum viewport fit")
    required=bool(dx or dy)
    if g["fit_required"]!=required or g["content_inside_viewport"]==required:
        raise ValueError("geometry fit flags disagree with native bounds")
    w=rects["window_rect"]
    if (w["x"]<c["x"]-tolerance or w["y"]<c["y"]-tolerance or
            w["x"]+w["width"]>c["x"]+c["width"]+tolerance or
            w["y"]+w["height"]>c["y"]+c["height"]+tolerance):
        raise ValueError("content union does not include the original window root")
    if value.get("status")=="already_layout_fitted_verification_pending" and (required or value["dispatch_invoked"]):
        raise ValueError("already-fitted status cannot dispatch or retain an outside layout")
