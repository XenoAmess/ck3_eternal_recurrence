"""Pure audience view of validated display cards and actual receipt phases."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import unicodedata

from decision_display_contract_v1 import (
    DETAIL, DisplayCard, Record, action_name, chinese_lines, exact_int,
    is_observation, maybe_record, outcome, parse_card, record,
)

TITLE = "智能体实时决策"


def decode(row: object) -> Record:
    data = record(row)
    if data.get("tool") == "root_before_auto_turn_submit":
        return maybe_record(data.get("body"))
    result = maybe_record(data.get("result"))
    body = result.get("structured_content", result.get("structuredContent"))
    if isinstance(body, dict):
        return record(body)
    blocks = result.get("content")
    if isinstance(blocks, list):
        for item in blocks:
            block = maybe_record(item)
            if block.get("type") != "text" or not isinstance(block.get("text"), str):
                continue
            try:
                parsed: object = json.loads(str(block["text"]))
            except (ValueError, TypeError):
                continue
            if isinstance(parsed, dict):
                return record(parsed)
    return {}


def action(step: object) -> str:
    return action_name(step)


def clean_chinese(value: object, limit: int = 1600) -> str:
    return " ".join(chinese_lines(value, limit=limit))[:limit]


def reason(plan: object, step: object) -> str:
    data = maybe_record(plan)
    rich = maybe_record(data.get("war_decision_presentation_v1"))
    if rich.get("selected_step") == step and rich.get("phase") == data.get("phase"):
        readable = clean_chinese(rich.get("reason"))
        if readable:
            return readable
    readable = clean_chinese(data.get("reason"))
    if readable:
        return readable
    if isinstance(step, str) and step.startswith("life-advance"):
        return "当前计划选择继续观察，出现新局势后重新决策。"
    return "本条未提供可直接展示的中文理由，具体取舍尚不明确。"


def result_text(body: object) -> str:
    return outcome(body).text


@dataclass
class BusinessEvent:
    namespace: str
    sequence: int
    callback_index: int | None
    digest: str | None
    step: str
    action: str
    result: str


class AudienceState:
    def __init__(self) -> None:
        self.stage = "观察当前游戏"
        self.decision = "核对当前局势"
        self.reason = "继续已有战役，保留本次进度。"
        self.result = "等待当前地图与实际回执。"
        self.events: list[BusinessEvent] = []
        self.card: DisplayCard | None = None
        self.detail_unavailable = False
        self.observation = ""
        self.repair: str | None = None
        self.last_key = (0, -1)

    def switch_namespace(self) -> None:
        self.last_key = (0, -1)

    def _history(self, *, row: Record, request: Record, number: int, step: str,
                 planned: bool, description: str) -> None:
        if is_observation(step):
            return
        namespace = row.get("source_namespace")
        namespace = namespace if isinstance(namespace, str) else ""
        callback = request.get("callback_index")
        if callback is not None:
            callback = exact_int(callback, "callback_index", minimum=1)
        digest = row.get("actual_observation_sha256", request.get("actual_observation_sha256"))
        digest = digest if isinstance(digest, str) and len(digest) == 64 else None
        matches = [item for item in self.events if item.namespace == namespace
                   and item.sequence == number and item.step == step
                   and (callback is None or item.callback_index == callback)
                   and (digest is None or item.digest == digest)]
        # Exact callback identity, or a single unambiguous same-step legacy plan.
        # Never mark every child of one AUTO request successful.
        if len(matches) == 1 and (not planned or callback is not None or digest is not None):
            matches[0].result = description
            return
        if not planned and matches:
            return
        self.events.append(BusinessEvent(namespace, number, callback, digest, step,
                                         self.decision, description))
        self.events = self.events[-3:]

    def consume(self, row: object) -> None:
        data = record(row)
        if data.get("root_runtime_repair_status"):
            return
        body = decode(data)
        plan = maybe_record(body.get("plan"))
        selected = body.get("selected_step") or body.get("step") or plan.get("selected_step")
        step = selected if isinstance(selected, str) else ""
        request = maybe_record(data.get("request"))
        tool_value = request.get("tool", data.get("tool", ""))
        tool = tool_value if isinstance(tool_value, str) else ""
        number = request.get("sequence")
        if number is None and tool == "root_before_auto_turn_submit":
            number = request.get("parent_sequence")
        sequence = exact_int(number, "sequence", minimum=1) if number is not None else 0
        planned = tool in ("root_before_auto_turn_submit", "ck3_plan_turn")
        if sequence:
            key = (sequence, 0 if planned else 1)
            if key < self.last_key:
                return
            self.last_key = key
        error_result = maybe_record(data.get("result"))
        if data.get("client_error") or error_result.get("is_error", error_result.get("isError")):
            self.result = "请求失败；原操作是否生效仍未知，不重复提交。"
            if step:
                self._history(row=data, request=request, number=sequence, step=step,
                              planned=False, description=self.result)
            return
        if any(token in tool for token in ("bookmark", "frontend", "new_game", "start_game")):
            if "query" in tool:
                self.decision = "确认菜单与开局状态"
            elif "bookmark" in tool:
                self.decision = "选择开局角色"
            else:
                self.decision = "开始新的战役"
            self.reason = "从1066年书签建立一局干净的新游戏。"
            self.result = result_text(body)
            self.card = None
            self.detail_unavailable = False
            return
        observed = is_observation(step)
        if observed and self.events:
            self.observation = "核对：" + result_text(body)
            return
        if planned or tool == "ck3_auto_turn" or step:
            self.stage = "自动游玩"
            self.decision = action(step)
            self.reason = reason(plan, step)
            self.result = "计划已形成，尚未提交。" if planned else result_text(body)
            # A result with the same step retains the plan detail if its compact
            # omitted that plan. Different steps never inherit a stale card.
            if plan:
                self.card = None
                self.detail_unavailable = DETAIL in plan
                if DETAIL in plan:
                    try:
                        self.card = parse_card(plan[DETAIL], step=step, phase=plan.get("phase"))
                    except ValueError:
                        pass
                    else:
                        self.detail_unavailable = False
            elif self.card is not None and self.card.selected_step != step:
                self.card = None
                self.detail_unavailable = False
            if self.card is not None:
                self.decision = self.card.action
                self.reason = " ".join(self.card.rationale)
            self.observation = ""
            if step:
                self._history(row=data, request=request, number=sequence, step=step,
                              planned=planned, description=self.result)

    def repair_status(self, state: object, binding: object, now: datetime | None = None) -> None:
        if not state:
            self.repair = None
            return
        data, expected = record(state), record(binding)
        active = maybe_record(data.get("active_binding", data.get("binding")))
        if any(active.get(key) != expected.get(key) for key in ("session", "game_pid", "game_creation_filetime")):
            self.repair = None
            return
        phase = data.get("phase")
        if data.get("withdrawn") or phase == "expired":
            self.repair = None
            return
        brief = clean_chinese(data.get("pause_reason"), 120) or "自动推进暂时停止"
        if phase in ("repairing", "repair_applied_waiting_for_progress"):
            self.repair = brief + "\n正在修复中"
            return
        proof = maybe_record(data.get("recovery_proof"))
        delta = proof.get("actual_date_delta_raw")
        if phase == "resolved" and type(delta) is int and delta > 0:
            end = data.get("expires_at_utc")
            if isinstance(end, str) and datetime.fromisoformat(end) <= (now or datetime.now(timezone.utc)):
                self.repair = None
                return
            self.repair = (clean_chinese(data.get("repair_message"), 120) or "修复已完成") + "\n已恢复推进"
        else:
            self.repair = None

    def render(self) -> str:
        """Fit a finite card at the unchanged 24px font; protect risks/outcome.

        Wide characters consume two layout cells. At 52 cells the actual
        Microsoft YaHei 24px replay stays inside 760px. The 36-line budget
        leaves vertical room inside 1300px; optional detail/history goes first.
        """
        def wrapped(value: str) -> list[str]:
            result: list[str] = []
            for paragraph in value.splitlines() or [""]:
                line = ""
                cells = 0
                for character in paragraph:
                    width = 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1
                    if cells + width > 52 and line:
                        result.append(line)
                        line, cells = "", 0
                    line += character
                    cells += width
                result.append(line)
            return result

        prefix = [TITLE, self.stage, "", "决策：" + self.decision]
        suffix = ["结果：" + self.result]
        if self.observation:
            suffix.append(self.observation)
        if self.repair:
            suffix += ["", self.repair]
        risks = ["风险：" + value for value in self.card.risks] if self.card is not None else []
        chosen: list[str] = []

        def fits(values: list[str]) -> bool:
            return sum(len(wrapped(value)) for value in prefix + values + risks + suffix) <= 36

        def offer(value: str) -> None:
            if fits([*chosen, value]):
                chosen.append(value)

        if self.card is not None:
            card = self.card
            # Costs and main rationale have precedence over old history and alternatives.
            for value in card.costs:
                offer("代价：" + value)
            for value in card.rationale:
                offer("理由：" + value)
            if card.target is not None:
                offer("目标：" + card.target)
            for value in card.facts[:2]:
                offer("局势：" + value)
            if card.alternatives:
                for value in card.alternatives[:2]:
                    offer("备选：" + value)
            elif card.alternatives is None and card.domain not in ("observation", "other"):
                offer("备选：本条没有提供候选比较资料。")
        else:
            offer("理由：" + self.reason)
            if self.detail_unavailable:
                offer("详情暂不可用；本条详情格式或绑定未通过校验。")
        history_events = self.events[:-1]
        if history_events:
            history = ["", "最近业务"] + [event.action + "：" + event.result for event in history_events[-2:]]
            if fits([*chosen, *history]):
                chosen += history
        # Current risk and independent verification state are never trimmed.
        return "\n".join(line for value in prefix + chosen + risks + suffix for line in wrapped(value))
