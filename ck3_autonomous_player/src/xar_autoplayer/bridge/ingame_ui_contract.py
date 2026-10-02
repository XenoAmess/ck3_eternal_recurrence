"""Four explicit native presentation routes; no planner/desktop fallback."""
from __future__ import annotations
import math
from .public_unit_contract import public_cunit_id

NAVIGATE_STEP = "navigate-ingame-ui-v1"
QUERY_STEP = "query-ingame-ui-window-v1"
NAVIGATE_CAPABILITY = "game.command.navigate-ingame-ui-v1"
QUERY_CAPABILITY = "game.command.query-ingame-ui-window-v1"
KINDS = {"character", "army", "combat", "knights"}
OPERATIONS = {"open_character": "character", "select_army": "army", "open_combat": "combat", "open_knights": "knights",
              "hover_left_knights":"combat", "hover_right_knights":"combat", "fit_combat_window":"combat"}


def validate_ui_request(operation: str, kind: str, subject_id: int, revision: int) -> None:
    if kind not in KINDS or (operation != "query" and OPERATIONS.get(operation) != kind):
        raise ValueError("unsupported typed UI operation/window")
    if isinstance(revision, bool) or not isinstance(revision, int) or not 0 <= revision < 2**64:
        raise ValueError("expected_revision must be uint64")
    if isinstance(subject_id, bool) or not isinstance(subject_id, int):
        raise ValueError("subject ID must be a full uint32 handle")
    if operation in {"query", "open_knights"}:
        if subject_id != 0:
            raise ValueError("this operation has no caller-selected subject")
    elif operation == "select_army":
        public_cunit_id(subject_id, "subject public CUnitID")
    elif not 0 < subject_id < 2**32 - 1:
        raise ValueError("subject ID must be positive and exclude the invalid handle")


def normalize_ui_result(value: object, *, operation: str, kind: str, subject_id: int,
                        native_revision: int, date_raw: int, actor_id: int) -> dict[str, object]:
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
    for key in ("current_subject_id", "native_army_id", "owner_character_id", "thread_id", "pump_epoch"):
        n = value.get(key)
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
    if value["available"]:
        if (not value["application_owner_thread_verified"] or not value["gui_owner_binding_verified"] or
                not value["gui_context_address"] or not value["gui_owner_address"]):
            raise ValueError("native UI original application/GUI binding unverified")
        if not value["thread_id"] or not value["pump_epoch"] or not value["window_exists"]:
            raise ValueError("native UI lacks owner/target-window observation")
        if operation == "query":
            if value.get("status") != "observed" or value["dispatch_invoked"] or value["verification_pending"]:
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
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 512 or not isinstance(widgets, list) or len(widgets) != count:
        raise ValueError("native census count/bound mismatch")
    if value["available"] and (not tree["root_available"] or count < 1 or tree.get("scope_root_name") != value.get("window_name")):
        raise ValueError("native census is not scoped to the target window")
    for widget in widgets:
        if (not isinstance(widget,dict) or not isinstance(widget.get("runtime_name"),str) or not isinstance(widget.get("child_path"),str) or
                type(widget.get("effective_visible")) is not bool or type(widget.get("enabled")) is not bool):
            raise ValueError("native census widget fields malformed")
        for key in ("depth","child_count","vtable_rva"):
            n=widget.get(key)
            if isinstance(n,bool) or not isinstance(n,int) or n<0:
                raise ValueError("native census widget integer malformed")
    if value["available"] and (widgets[0]["runtime_name"]!=value["window_name"] or widgets[0]["depth"]!=0 or
                               widgets[0]["effective_visible"]!=value["effective_visible"]):
        raise ValueError("native census root differs from target-window observation")
    if value.get("knights_list_scope") != "military_eligible_not_active_combat_roster":
        raise ValueError("native knights list scope missing")
    if (value.get("native_backend_id") != "ck3-1.19.0.6-native-ingame-ui-v1" or value.get("game_version") != "1.19.0.6" or
            value.get("executable_sha256") != "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"):
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
    return dict(value)


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
