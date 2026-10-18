"""Historical decision formatting helpers; legacy blue-window CLI is retired."""
from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import os
import sys
import time
import traceback
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone


class OverlayEvidence:
    """Keep one first exception and one closure receipt, without an event log."""

    def __init__(self, session, game_pid):
        self.session = Path(session)
        self.game_pid = game_pid
        self.overlay_pid = os.getpid()
        self.first_exception = None
        self.exception_count = 0
        self.exit_reason = None

    def _write(self, suffix, payload):
        path = self.session / f"ROOT-DECISION-OVERLAY-{self.overlay_pid}-{suffix}.json"
        with path.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        return str(path)

    def note_exception(self, error, stage):
        self.exception_count += 1
        if self.first_exception is not None:
            return
        self.first_exception = {
            "at_utc": datetime.now(timezone.utc).isoformat(), "stage": stage,
            "type": type(error).__name__, "message": str(error)[:2048],
            "errno": getattr(error, "errno", None), "winerror": getattr(error, "winerror", None),
            "traceback": "".join(traceback.format_exception(error))[-8192:],
        }
        payload = {"game_pid": self.game_pid, "overlay_pid": self.overlay_pid,
                   "first_exception": self.first_exception}
        try:
            self._write("FIRST-EXCEPTION", payload)
        except OSError as capture_error:
            payload["evidence_write_error"] = str(capture_error)[:2048]
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)

    def stop_reason(self, code):
        if self.exit_reason is None:
            self.exit_reason = {"code": code, "at_utc": datetime.now(timezone.utc).isoformat()}

    def write_closed(self):
        self.stop_reason("native_message_loop_returned_without_requested_stop")
        payload = {"at_utc": datetime.now(timezone.utc).isoformat(),
                   "game_pid": self.game_pid, "overlay_pid": self.overlay_pid,
                   "exit_reason": self.exit_reason, "first_exception": self.first_exception,
                   "exception_count": self.exception_count}
        try:
            self._write("CLOSED", payload)
        except OSError as error:
            payload["evidence_write_error"] = str(error)[:2048]
            print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)


def publish_decision_payload(decision_text, payload, evidence, retry_delays=(.02, .05, .1)):
    """Defer a locked destination to the next tick; retain the prior text."""
    if len(payload) > 32768:
        raise ValueError("decision text exceeded its finite byte limit")
    temporary = decision_text.with_name(decision_text.name + f".{os.getpid()}.{uuid.uuid4().hex}.pending")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
        for attempt in range(len(retry_delays) + 1):
            try:
                os.replace(temporary, decision_text)
                return True
            except PermissionError as error:
                evidence.note_exception(error, "decision_text_atomic_replace")
                if attempt == len(retry_delays):
                    return False
                time.sleep(retry_delays[attempt])
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def show_read_error(window, publish, evidence, error):
    evidence.note_exception(error, "tick")
    operations = (
        ("error_hide", lambda: window.set_content_visible(False)),
        ("error_publish", lambda: publish("决策数据暂不可用：" + type(error).__name__
                                         + "。此前内容仅为最后已知回执，未确认新的成功动作。")),
        ("error_render", lambda: window.update("回执读取暂不可用：" + type(error).__name__,
                                             "实时决策 · 数据暂不可用")),
    )
    for stage, operation in operations:
        try:
            operation()
        except Exception as secondary:
            evidence.note_exception(secondary, stage)


def close_panel(window, publish, evidence, code, message):
    evidence.stop_reason(code)
    for stage, operation in (
        ("stop_publish", lambda: publish(message + "此前内容仅为最后已知回执。")),
        ("stop_hide", lambda: window.set_content_visible(False)),
        ("stop_destroy", window.destroy),
    ):
        try:
            operation()
        except Exception as error:
            evidence.note_exception(error, stage)


def finish_overlay(window, publish, release_game_handle, evidence):
    evidence.stop_reason("native_message_loop_returned_without_requested_stop")
    for stage, operation in (
        ("final_publish", lambda: publish("面板 owner 已结束。此前内容仅为最后已知回执，未确认新的成功动作。")),
        ("final_window_close", window.close),
        ("final_game_handle_release", release_game_handle),
    ):
        try:
            operation()
        except Exception as error:
            evidence.note_exception(error, stage)
    evidence.write_closed()


def outcome_text(body):
    inner = body.get("result") if isinstance(body.get("result"), dict) else body
    if inner.get("checkpoint", {}).get("status") == "saved":
        return "存档文件已确认"
    status = inner.get("status", body.get("status", ""))
    return {"submitted": "已提交，等待读回", "executed": "本步骤已返回",
            "available": "查询已返回", "enacted": "已读回施行结果",
            "centered": "镜头位置已读回", "already_centered": "镜头已在目标处",
            "blocked": "受阻", "rejected": "已拒绝"}.get(status, status or "已返回")


def camera_presentation_text(camera):
    """Render asynchronous receipts without confusing queued ACK with success."""
    if not isinstance(camera, dict):
        return ""
    previous = camera.get("latest_actual")
    if isinstance(previous, dict) and isinstance(previous.get("receipt"), dict):
        camera = previous["receipt"]
    mode = camera.get("display_mode", camera.get("mode"))
    if mode not in {"realm", "hotspot"}:
        return "" if camera.get("status") == "scheduled" else "镜头跟随：" + outcome_text(camera)
    text = "全境镜头" if mode == "realm" else "战争热点镜头"
    actual = camera.get("native_actual")
    if isinstance(actual, dict):
        if actual.get("camera_postcondition_verified") is True:
            text += "：原生位置已稳定"
        elif actual.get("status") == "submitted":
            text += "：已提交，等待稳定"
        else:
            text += "：" + str(actual.get("status", "等待回执"))
        if mode == "realm" and actual.get("county_count"):
            text += f" · {actual['county_count']} 县（含封臣领地）"
    else:
        text += "：等待原生回执"
    return text


def decode(row):
    if not isinstance(row, dict):
        raise ValueError("Response is not a JSON object")
    if (row.get("tool") == "root_before_auto_turn_submit"
            and isinstance(row.get("body"), dict)):
        return {}, row["body"]
    result = row.get("result", {})
    if not isinstance(result, dict):
        raise ValueError("Response result is not a JSON object")
    body = result.get("structured_content", result.get("structuredContent"))
    if not isinstance(body, dict):
        for item in result.get("content", []):
            if item.get("type") == "text":
                try:
                    body = json.loads(item["text"])
                    break
                except ValueError:
                    pass
    return result, body if isinstance(body, dict) else {}


def action_name(step):
    exact = {
        "query-declarable-wars": "查找当前可宣战目标",
        "query-army-strengths-v1": "读取真实军力与部队构成",
        "raise-troops-default": "在集结点召集部队",
        "life-advance": "推进时间并观察局势变化",
        "save-checkpoint": "保存当前局面",
        "center-map-on-landed-title-v1": "将镜头对准战争热点",
        "enact-realm-law-crown-v1-private": "提升王权",
        "verify-realm-law-crown-v1-private": "独立确认王权变更",
        "private-submit-player-construction-v1": "按预算启动建筑施工",
        "private-query-player-construction-receipt-v1": "检查建筑施工与完工状态",
    }
    if step in exact:
        return exact[step]
    if isinstance(step, str):
        for prefix, text in (
            ("declare-war-", "向选定目标宣战"),
            ("query-war-entry-assessments-", "比较目标与我方的战略兵力"),
            ("query-war-termination-options-", "核对战争结束条件"),
            ("select-event-option-", "选择事件选项"),
            ("move-army-", "指挥军队移动"),
            ("preview-move-army-", "预览行军路线"),
            ("query-route-contact-horizon-v1-", "核对行军途中的接敌时序"),
            ("query-combat-", "评估战斗"),
        ):
            if step.startswith(prefix):
                return text
    return step or "等待实际规划结果"


def reason_text(plan):
    phase = plan.get("phase", "")
    reasons = {
        "native_war_discovery": "先读取当前合法目标，再选择战争。",
        "native_war_entry_assessment": "宣战前比较真实战略兵力。",
        "native_war_entry_assessment_alternative": "当前目标评估依赖额外战略力量；继续比较其他合法目标。",
        "native_war_declaration": "宣战前核对当前兵力、潜在敌方联军和风险政策。",
        "native_war_entry_forecast_required": "当前兵力与联军评估尚未授权本次宣战；本轮不宣战。",
        "native_war_raise": "战争已实际存在，但还没有可控制军队；先召集部队。",
        "native_war_gathering_progress": "部队仍在集结；推进时间，完成后再指挥移动。",
        "native_war_termination_query": "先核对战争分数、对方响应和结束条件。",
        "crown_ordinary_typed_enact": "当前王权升级在原生报价下得到正向策略评分。",
        "crown_independent_receipt": "上一项王权动作已提交；读取独立结果，避免重复提交。",
    }
    reasons["native_war_army_strength_query"] = "先读取双方现有兵力、原生军力与补员信息，再决定进攻路线。"
    reasons["native_war_route_preview"] = "移动前按当前日期和起点核对通往战争目标的实际路线。"
    reasons["native_war_candidate_contact_horizon"] = "路线存在交叉，先核对未来一天双方到达与接敌时序。"
    reasons["native_war_capital_regroup_hold_progress"] = "进攻路线均不安全，暂守当前首都，推进后重评战争与路线。"
    summary = reasons.get(phase, plan.get("reason") or "等待实际决策理由。")
    presentation = plan.get("war_decision_presentation_v1")
    if (isinstance(presentation, dict) and isinstance(presentation.get("reason"), str)
            and presentation["reason"].strip()
            and presentation.get("phase") == phase
            and presentation.get("selected_step") == plan.get("selected_step")):
        return presentation["reason"][:1200] + "\n" + summary
    return summary


def war_reason(plan):
    summary = reason_text(plan)
    admission = plan.get("prewar_force_admission")
    v2_present = "prewar_force_admission" in plan
    if v2_present:
        admission = admission if isinstance(admission, dict) else {}
        risk = admission.get("force_risk")
        risk = risk if isinstance(risk, dict) else {}
        policy = risk.get("policy")
        policy = policy if isinstance(policy, dict) else {}
        lower, upper = risk.get("actor_lower_soldiers"), risk.get("enemy_upper_soldiers")
        numerator = policy.get("minimum_actor_to_enemy_ratio_numerator")
        denominator = policy.get("minimum_actor_to_enemy_ratio_denominator")
        qualified = (risk.get("status") == "qualified"
                     and risk.get("force_risk_qualified") is True
                     and type(lower) is int and lower >= 0
                     and type(upper) is int and upper >= 0
                     and type(numerator) is int and numerator > 0
                     and type(denominator) is int and denominator > 0)
        if qualified:
            summary += f"\n我方当前可执行动员下界 {lower} 人；完整潜在初始敌方联军库存上界 {upper} 人。"
            summary += ("\n我方下界取已证明可召集的未召集兵力与已召集且可指挥兵力的较大值，"
                        "不叠加未证明互斥的部队。")
            summary += ("\n敌方上界覆盖全部已观察潜在初始参战者的当前库存；"
                        "不预测未来招募、补员、雇佣或到达时序。")
            summary += (f"\n整数政策门槛 {numerator}/{denominator}："
                        f"我方下界 × {denominator} ≥ 敌方上界 × {numerator}。"
                        "这是风险余量政策，不是胜率或战斗保证。")
        else:
            summary += "\n当前兵力风险准入未确认；不从旧代理值或简化推演补足资格。"
        if (not qualified or admission.get("status") != "qualified"
                or admission.get("declare_admitted") is not True):
            actual_reason = admission.get("reason") or risk.get("reason") or plan.get("reason")
            summary += "\n实际未准入原因：" + str(actual_reason or "准入数据缺失或格式不合格")
        missing = risk.get("missing_required_domains")
        if isinstance(missing, list) and missing:
            summary += "\n缺失证据域：" + "、".join(value for value in missing if isinstance(value, str))
    assessment = plan.get("war_entry_assessment", {})
    assessment = assessment if isinstance(assessment, dict) else {}
    actor = assessment.get("actor_power_total_raw")
    target = assessment.get("target_power_total_raw")
    historical = []
    if type(actor) in (int, float) and type(target) in (int, float) and actor >= 0 and target > 0:
        historical.append(f"综合军力代理约为目标的 {actor / target:.2f} 倍（非士兵数）")
    forecast = plan.get("prewar_battle_forecast", {})
    forecast = forecast if isinstance(forecast, dict) else {}
    wins, samples = forecast.get("wins"), forecast.get("sample_count")
    if type(wins) is int and type(samples) is int and 0 <= wins <= samples and samples > 0:
        historical.append(f"简化推演 {wins}/{samples} 占优")
    if historical:
        summary += "\n历史诊断" + ("（不作为本次宣战理由）" if v2_present else "（不代表当前准入或战果）")
        summary += "：" + "；".join(historical) + "。"
    return summary


def main():
    raise SystemExit(
        "Legacy blue decision overlay is retired (2026-10-18 user instruction). "
        "Do not start it for new recordings. Actual decision observation and "
        "publication helpers remain available; see the retirement migration note."
    )


if __name__ == "__main__":
    main()
