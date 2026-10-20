"""Versioned audience display contract. Import performs no I/O.

The display is a projection of supplied receipts, never an action or a verifier.
Unknown details stay unknown; the original plan and source guards remain primary.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal, TypedDict

Record = dict[str, object]
Domain = Literal["war", "event", "construction", "diplomacy", "family", "realm", "observation", "other"]
Stage = Literal["planned", "submitted", "observed", "verified", "not_submitted", "unknown", "returned"]
SCHEMA: Literal["xar.decision-display/v1"] = "xar.decision-display/v1"
DETAIL = "decision_display_v1"
UNAVAILABLE = "decision_display_unavailable_v1"
SOFT_DISPLAY_BYTES = 12000


class DisplayUnavailableWire(TypedDict):
    schema: Literal["xar.decision-display-unavailable/v1"]
    status: Literal["detail_unavailable"]
    error_type: Literal["ValueError", "TypeError", "OverflowError"]



class DisplayWire(TypedDict):
    schema: Literal["xar.decision-display/v1"]
    selected_step: str
    phase: str | None
    domain: Domain
    action: str
    target: str | None
    facts: list[str]
    rationale: list[str]
    alternatives: list[str] | None
    costs: list[str]
    risks: list[str]


@dataclass(frozen=True)
class DisplayCard:
    selected_step: str
    phase: str | None
    domain: Domain
    action: str
    target: str | None
    facts: tuple[str, ...]
    rationale: tuple[str, ...]
    alternatives: tuple[str, ...] | None
    costs: tuple[str, ...]
    risks: tuple[str, ...]

    def wire(self) -> DisplayWire:
        return {"schema": SCHEMA, "selected_step": self.selected_step, "phase": self.phase,
                "domain": self.domain, "action": self.action, "target": self.target,
                "facts": list(self.facts), "rationale": list(self.rationale),
                "alternatives": None if self.alternatives is None else list(self.alternatives),
                "costs": list(self.costs), "risks": list(self.risks)}


@dataclass(frozen=True)
class Outcome:
    stage: Stage
    text: str


def record(value: object) -> Record:
    """Narrow a dynamic JSON object without unchecked casts or Any contracts."""
    if not isinstance(value, dict):
        raise ValueError("object required")
    result: Record = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("object key must be a string")
        result[key] = item
    return result


def maybe_record(value: object) -> Record:
    return record(value) if isinstance(value, dict) else {}


def exact_int(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > 2**53 - 1:
        raise ValueError(name + " must be a safe exact integer")
    return value


def text(value: object, name: str, *, nullable: bool = False, limit: int = 1600) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(name + " must be bounded nonempty text")
    return value


def lines(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 8:
        raise ValueError(name + " must be a bounded JSON list")
    result: list[str] = []
    for item in value:
        line = text(item, name)
        if line is None:
            raise ValueError(name + " cannot contain null")
        result.append(line)
    return tuple(result)


def parse_card(value: object, *, step: str, phase: object) -> DisplayCard:
    data = record(value)
    required = {"schema", "selected_step", "phase", "domain", "action", "target",
                "facts", "rationale", "alternatives", "costs", "risks"}
    if set(data) != required or data["schema"] != SCHEMA:
        raise ValueError("unknown or incomplete display contract")
    if data["selected_step"] != step or data["phase"] != phase:
        raise ValueError("display identity differs from actual plan")
    domain = data["domain"]
    if domain not in ("war", "event", "construction", "diplomacy", "family", "realm", "observation", "other"):
        raise ValueError("unknown domain")
    # Literal narrowing stays explicit at this JSON boundary.
    if domain == "war": d: Domain = "war"
    elif domain == "event": d = "event"
    elif domain == "construction": d = "construction"
    elif domain == "diplomacy": d = "diplomacy"
    elif domain == "family": d = "family"
    elif domain == "realm": d = "realm"
    elif domain == "observation": d = "observation"
    else: d = "other"
    selected = text(data["selected_step"], "selected_step")
    action = text(data["action"], "action", limit=120)
    if selected is None or action is None:
        raise ValueError("required display text missing")
    alternatives = data["alternatives"]
    risks = lines(data["risks"], "risks")
    if len(risks) > 2 or any(len(value) > 200 for value in risks):
        raise ValueError("current risks exceed the finite display contract")
    return DisplayCard(selected, text(data["phase"], "phase", nullable=True), d, action,
                       text(data["target"], "target", nullable=True, limit=240),
                       lines(data["facts"], "facts"), lines(data["rationale"], "rationale"),
                       None if alternatives is None else lines(alternatives, "alternatives"),
                       lines(data["costs"], "costs"), risks)


def chinese_lines(value: object, *, limit: int = 1600) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    hidden = ("PID", "creation_filetime", "native_revision", "snapshot_id", "sdk-",
              "SourceSHA", "XAR_", "query-", "罗贝尔的30年")
    output: list[str] = []
    for line in value.splitlines():
        if any(token in line for token in hidden):
            continue
        line = line.replace("state_changed", "局势发生变化").replace("SDK", "游戏接口").replace("Native", "游戏")
        if any("\u4e00" <= character <= "\u9fff" for character in line):
            output.append(line.strip()[:limit])
    return tuple(output[:8])


def action_name(step: object) -> str:
    if not isinstance(step, str) or not step:
        return "观察当前局势"
    for prefixes, label in (
        (("advance-route-contact-window-v1-",), "保持现有行军，按短窗口停下复查"),
        (("life-advance", "exact-one-day"), "推进时间，观察局势变化"),
        (("declare-war-",), "向选定目标宣战"),
        (("move-army-", "halt-army-"), "调整军队行动"),
        (("select-event-option", "resolve-mandatory", "choose-"), "处理当前事件选择"),
        (("save-checkpoint", "save-"), "保存本次进度"),
        (("raise-troops", "raise-army"), "集结军队"),
        (("center-map", "camera-"), "调整观察镜头"),
        (("ordinary-sway", "private-submit-sway"), "开始拉拢目标角色"),
        (("private-query-sway",), "核对拉拢计谋的实际结果"),
        (("query-", "preview-", "verify-"), "核对当前局势与行动条件"),
    ):
        if step.startswith(prefixes):
            return label
    if "construction" in step or "building" in step:
        return "检查或安排领地建设"
    if any(key in step for key in ("family", "guardian", "education", "focus")):
        return "处理家族与教育事务"
    if "crown" in step or "realm-law" in step:
        return "处理领地政务"
    return "处理当前游戏事务"


def is_observation(step: object) -> bool:
    return isinstance(step, str) and (step.startswith(("query-", "preview-", "verify-", "camera-", "center-map"))
                                     or "query-" in step or "receipt" in step)


def _domain(step: str, phase: object) -> Domain:
    if "war" in str(phase) or any(key in step for key in ("army", "troops", "route-contact", "mercenary")):
        return "war"
    if "event" in step: return "event"
    if "construction" in step or "building" in step: return "construction"
    if "sway" in step or "diploma" in step: return "diplomacy"
    if any(key in step for key in ("family", "guardian", "education", "focus")): return "family"
    if "crown" in step or "realm-law" in step: return "realm"
    return "observation" if is_observation(step) else "other"


def project_card(actual: object) -> DisplayCard:
    """Produce one detached card; use the SDK's existing strict route parser.

    No command, native call, file read, translation service or model is used.
    A missing SDK parser leaves the route detail unknown instead of guessing.
    """
    plan = record(actual)
    selected = text(plan.get("selected_step"), "selected_step")
    if selected is None:
        raise ValueError("selected step missing")
    phase = text(plan.get("phase"), "phase", nullable=True)
    if DETAIL in plan:
        return parse_card(plan[DETAIL], step=selected, phase=phase)
    rationale = list(chinese_lines(plan.get("reason")))
    facts: list[str] = []
    costs: list[str] = []
    risks: list[str] = []
    target: str | None = None
    action = action_name(selected)
    if selected.startswith("advance-route-contact-window-v1-"):
        try:
            from xar_autoplayer.bridge.route_contact_window_contract import parse_advance_route_contact_window_step
        except ImportError:
            parsed = None
        else:
            parsed = parse_advance_route_contact_window_step(selected)
        if parsed is not None:
            _, _, hostiles, days = parsed
            action = f"保持现有行军，最多推进{days}天"
            target = "当前已选行军目标"
            facts = [f"当前计划绑定1支移动军队、{len(hostiles)}支敌军的接敌范围。"]
            rationale = ["按当前计划的短窗口推进，随后重新核对敌我行军与接敌局势。",
                         "计划在实际到达、目标改变、交战、撤退或暂停变化时停下复查。"]
            risks = ["这些是计划停点；实际推进天数与暂停结果仍须原生后验确认。"]
        else:
            risks = ["行军窗口详情未取得，不能确认计划天数或敌军范围。"]
    presentation = maybe_record(plan.get("war_decision_presentation_v1"))
    if (presentation.get("phase") == phase and presentation.get("selected_step") == selected):
        rich = chinese_lines(presentation.get("reason"))
        if rich:
            rationale = [*rich, *rationale][:8]
    construction = maybe_record(plan.get("construction_private_query"))
    candidate = maybe_record(construction.get("candidate"))
    quote = candidate.get("stock_gold_cost_raw")
    if "stock_gold_cost_raw" in candidate:
        if type(quote) is not int or not 0 <= quote <= 2**63 - 1:
            raise ValueError("native gold quote must be a nonnegative signed int64")
        whole, fraction = divmod(quote, 100_000)
        costs.append(f"原生工程报价{whole}.{fraction:05d}金；尚未扣款不计为已支出。")
    cash = maybe_record(plan.get("wartime_construction_cash_v1"))
    if cash.get("new_spend_allowed") is False:
        risks.append("当前战争资金条件未放行可选建设，保留军费和应急资金。")
    if not rationale:
        if selected.startswith("life-advance"):
            rationale = ["当前计划选择继续观察，出现新局势后重新决策。"]
        elif is_observation(selected):
            rationale = ["先读取当前局势与合法条件，再决定后续行动。"]
        else:
            rationale = ["本条未提供可直接展示的中文理由；保留原计划，具体取舍尚不明确。"]
    if _domain(selected, phase) == "war" and not risks:
        risks = ["当前兵数不代表胜率；未来增援、抵达及战果未由本条计划确认。"]
    card = DisplayCard(selected, phase, _domain(selected, phase), action, target, tuple(facts),
                       tuple(rationale[:8]), None, tuple(costs), tuple(risks))
    # Exercise exactly the persisted JSON representation, including tuple/list.
    return parse_card(json.loads(json.dumps(card.wire(), ensure_ascii=False)), step=selected, phase=phase)


def _display_bytes(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _unavailable(error: ValueError | TypeError | OverflowError) -> DisplayUnavailableWire:
    kind: Literal["ValueError", "TypeError", "OverflowError"]
    if isinstance(error, OverflowError): kind = "OverflowError"
    elif isinstance(error, TypeError): kind = "TypeError"
    else: kind = "ValueError"
    return {"schema": "xar.decision-display-unavailable/v1",
            "status": "detail_unavailable", "error_type": kind}


def _required_step(plan: Record) -> None:
    step = plan.get("selected_step")
    if step is not None:
        text(step, "selected_step")
        if not isinstance(step, str) or len(step.encode("utf-8")) > 4096:
            raise ValueError("required selected-step identity exceeds its finite bound")


def _fallback_plan(plan: Record, error: ValueError | TypeError | OverflowError) -> Record:
    # Required source/action identity is validated before the optional boundary.
    result: Record = {DETAIL: None, UNAVAILABLE: _unavailable(error)}
    if "selected_step" in plan:
        result["selected_step"] = plan["selected_step"]
    for key, limit in (("reason", 1200),):
        value = plan.get(key)
        if isinstance(value, str):
            result[key] = value[:limit]
    return result


def project_plan(actual: object) -> Record:
    plan = record(actual)
    _required_step(plan)  # Never soften malformed business/action identity.
    result = {key: plan[key] for key in ("policy", "phase", "selected_step", "reason", "decision",
              "declaration", "prewar_force_admission", "event_choice_utility") if key in plan}
    for key in ("reason", "selected_step", "policy", "phase"):
        value = result.get(key)
        if isinstance(value, str):
            result[key] = value[:1200]
    try:
        presentation = record(plan["war_decision_presentation_v1"]) if "war_decision_presentation_v1" in plan else {}
        rich = presentation.get("reason")
        if "war_decision_presentation_v1" in plan:
            if (set(presentation) != {"phase", "selected_step", "reason"}
                    or presentation.get("phase") != plan.get("phase")
                    or presentation.get("selected_step") != plan.get("selected_step")
                    or not isinstance(rich, str)):
                raise ValueError("optional war presentation has wrong fields or binding")
        if isinstance(rich, str):
            result["war_decision_presentation_v1"] = {
                "phase": plan.get("phase"), "selected_step": plan.get("selected_step"),
                "reason": rich[:1600]}
        if plan.get("selected_step") is not None:
            result[DETAIL] = project_card(plan).wire()
        if _display_bytes(result) > SOFT_DISPLAY_BYTES:
            raise ValueError("optional projection exceeds finite display budget")
    except (ValueError, TypeError, OverflowError) as error:
        return _fallback_plan(plan, error)
    return result


def outcome(body: object) -> Outcome:
    outer = record(body)
    if UNAVAILABLE in outer:
        return Outcome("unknown", "展示或核验材料暂不可用；保留原始回执，实际结果仍待核对。")
    inner = maybe_record(outer.get("result")) or outer
    status = inner.get("status", outer.get("status"))
    if status == "observed_after_native_error" or inner.get("native_ack_status") == "unknown_after_error":
        return Outcome("unknown", "观察到新状态；原提交结果仍未确认，不能重复提交。")
    if status == "planned":
        return Outcome("planned", "计划已形成，尚未提交。")
    if status in ("submitted", "queued"):
        return Outcome("submitted", "已提交，等待独立结果核验。")
    if status in ("available", "hidden", "not_visible"):
        return Outcome("observed", "只读局势信息已读回。")
    proof = maybe_record(inner.get("postcondition"))
    if (proof.get("status") == "verified" and proof.get("independent_readback") is True
            and isinstance(proof.get("source_observation"), str) and proof["source_observation"]
            and isinstance(inner.get("action_request_id"), str) and inner["action_request_id"]
            and proof.get("action_request_id") == inner["action_request_id"]):
        return Outcome("verified", "独立后验已确认本步骤结果。")
    if status in ("blocked", "rejected", "failed", "readonly_unavailable", "error") or inner.get("accepted") is False:
        if inner.get("failure_stage") == "pre_submit" and inner.get("business_submitted") is False:
            return Outcome("not_submitted", "提交前条件未通过，已确认本次未提交。")
        return Outcome("unknown", "请求未完成核验；原操作是否生效仍未知，保留回执。")
    if maybe_record(inner.get("checkpoint")).get("status") == "saved":
        return Outcome("returned", "存档回执报告已保存；保留实际文件核对证据。")
    return Outcome("returned", "实际回执已返回，业务后验仍待核对。")


OUTCOME_KEYS = ("status", "step", "accepted", "checkpoint", "ending_date_raw", "post_date_raw",
                "actor_character_id", "native_ack_status", "postcondition", "failure_stage",
                "business_submitted", "action_request_id")


def project_result(row: object, body: object) -> Record:
    original, actual = record(row), record(body)
    _required_step(actual)
    plan = record(actual["plan"]) if isinstance(actual.get("plan"), dict) else None
    if plan is not None:
        _required_step(plan)
    result = {key: actual[key] for key in ("status", "selected_step", "step", "accepted", "camera_follow") if key in actual}
    if plan is not None:
        result["plan"] = project_plan(plan)
    inner = maybe_record(actual.get("result")) or actual
    small = {key: inner[key] for key in OUTCOME_KEYS if key in inner}
    try:
        if "postcondition" in small:
            record(small["postcondition"])
        for key, fields in (("active_wars", ("war_id", "player_side", "primary_opponent_character_id", "targeted_title_ids")),
                            ("army_strengths", ("army_id", "current_soldiers"))):
            values = inner.get(key)
            if isinstance(values, list):
                small[key] = [{name: entry[name] for name in fields if name in entry}
                              for value in values[:6] if (entry := maybe_record(value))]
        result["result"] = small
        projected = {"request": original.get("request"), "ended_at_utc": original.get("ended_at_utc"),
                     "source": "compact projection of this actual SDK result; raw response retained",
                     "result": {"is_error": False, "structured_content": result}}
        if _display_bytes(projected) > SOFT_DISPLAY_BYTES:
            raise ValueError("optional result projection exceeds finite display budget")
        return projected
    except (ValueError, TypeError, OverflowError) as error:
        # Keep request identity; drop optional display payload, never replay action.
        result = {key: value for key in ("selected_step", "step")
                  if isinstance(value := actual.get(key), str)
                  and (key == "selected_step" or len(value.encode("utf-8")) <= 1024)}
        if plan is not None:
            result["plan"] = _fallback_plan(plan, error)
        result[UNAVAILABLE] = _unavailable(error)
        request = maybe_record(original.get("request"))
        request = {key: request[key] for key in ("tool", "sequence", "parent_sequence",
                   "callback_index", "callback_protocol", "actual_observation_sha256") if key in request}
        return {"request": request, "ended_at_utc": original.get("ended_at_utc"),
                "source": "compact actual result; optional display unavailable; raw response retained",
                "result": {"is_error": False, "structured_content": result}}
