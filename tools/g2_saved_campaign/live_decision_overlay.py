"""Show actual Root file-queue plans, submissions and outcomes over the game."""
from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from decision_overlay_window import NativeOverlay


def outcome_text(body):
    inner = body.get("result") if isinstance(body.get("result"), dict) else body
    if inner.get("checkpoint", {}).get("status") == "saved":
        return "存档文件已确认"
    status = inner.get("status", body.get("status", ""))
    return {"submitted": "已提交，等待读回", "executed": "本步骤已返回",
            "available": "查询已返回", "enacted": "已读回施行结果",
            "blocked": "受阻", "rejected": "已拒绝"}.get(status, status or "已返回")


def decode(row):
    if not isinstance(row, dict):
        raise ValueError("Response is not a JSON object")
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
        "native_war_declaration": "当前合法宣战通过了战前模型的保守风险门槛。",
        "native_war_raise": "战争已实际存在，但还没有可控制军队；先召集部队。",
        "native_war_gathering_progress": "部队仍在集结；推进时间，完成后再指挥移动。",
        "native_war_termination_query": "先核对战争分数、对方响应和结束条件。",
        "crown_ordinary_typed_enact": "当前王权升级在原生报价下得到正向策略评分。",
        "crown_independent_receipt": "上一项王权动作已提交；读取独立结果，避免重复提交。",
    }
    reasons["native_war_army_strength_query"] = "先读取双方现有兵力、原生军力与补员信息，再决定进攻路线。"
    return reasons.get(phase, plan.get("reason") or "等待实际决策理由。")


def war_reason(plan):
    assessment = plan.get("war_entry_assessment", {})
    actor = assessment.get("actor_power_total_raw")
    target = assessment.get("target_power_total_raw")
    summary = reason_text(plan)
    if isinstance(actor, (int, float)) and isinstance(target, (int, float)) and target > 0:
        summary += f"\n战前综合军力约为目标的 {actor / target:.2f} 倍（非士兵数）。"
    forecast = plan.get("prewar_battle_forecast", {})
    wins, samples = forecast.get("wins"), forecast.get("sample_count")
    if isinstance(wins, int) and isinstance(samples, int) and samples > 0:
        summary += f"\n简化推演 {wins}/{samples} 占优；这是战前估计，不代表战果。"
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--campaign-label", default="当前自动游玩局")
    parser.add_argument("--target-label", action="append", default=[], metavar="ID=NAME")
    args = parser.parse_args()
    session = args.session.resolve()
    launch = json.loads((session / "ROOT-ACTUAL-GAME-LAUNCH.json").read_text(encoding="utf-8"))
    targets = {}
    for value in args.target_label:
        key, separator, label = value.partition("=")
        if not separator or not key.isdecimal() or not label:
            parser.error("target label must be ID=NAME")
        targets[int(key)] = label
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_uint64)] * 4
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.WaitForSingleObject.restype = ctypes.c_uint32
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x00101000, False, launch["pid"])
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    times = [ctypes.c_uint64() for _ in range(4)]
    if not kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
        kernel.CloseHandle(handle)
        raise ctypes.WinError(ctypes.get_last_error())
    created = times[0].value / 10_000_000 - 11_644_473_600
    expected = datetime.strptime(launch["creation_date"].split("+")[0], "%Y%m%d%H%M%S.%f").replace(tzinfo=timezone.utc)
    if abs(created - expected.timestamp()) > .001:
        kernel.CloseHandle(handle)
        raise RuntimeError("Game process generation differs from the launch receipt")
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.restype = ctypes.c_void_p
    foreground_before = user.GetForegroundWindow()
    window = NativeOverlay()
    hwnd = window.hwnd
    get_style = user.GetWindowLongPtrW
    get_style.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_style.restype = ctypes.c_ssize_t
    seen = set()
    records = []
    war_decision = None
    current = "等待新的真实回执"
    reason = ""
    last_render = None
    blocker = ""

    def tick():
        nonlocal war_decision, current, reason, last_render, blocker
        process_state = kernel.WaitForSingleObject(handle, 0)
        if process_state == 0 or (session / "STOP-DECISION-OVERLAY").exists():
            window.destroy()
            return
        if process_state != 258:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            for path in sorted((session / "responses").glob("*.json")):
                if path.name in seen:
                    continue
                if path.stat().st_size > 16 * 1024 * 1024:
                    seen.add(path.name)
                    current = "回执过大，悬浮窗跳过正文；原件保留"
                    continue
                row = json.loads(path.read_text(encoding="utf-8"))
                result, body = decode(row)
                plan = body.get("plan") if isinstance(body.get("plan"), dict) else {}
                step = body.get("selected_step") or body.get("step") or plan.get("selected_step")
                tool = row.get("request", {}).get("tool", "")
                stamp = row.get("ended_at_utc", "")
                try:
                    clock = datetime.fromisoformat(stamp).astimezone().strftime("%H:%M:%S") if stamp else "时间未记录"
                except (TypeError, ValueError):
                    clock = "时间格式无效"
                if result.get("is_error", result.get("isError")) or row.get("client_error"):
                    message = " ".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
                    if "army-strength result exceeds" in message:
                        current = "暂停：军力查询返回数据超过接口上限"
                        reason = message[:260]
                        blocker = current
                    else:
                        current = "暂停：接口返回错误"
                        reason = message[:260] or row.get("client_error", "")
                    records.append(f"{clock} 失败 · {current}")
                elif tool == "ck3_plan_turn":
                    current = "计划中 · " + action_name(step)
                    reason = reason_text(plan)
                    records.append(f"{clock} 计划 · {action_name(step)}")
                elif tool == "ck3_auto_turn" or step:
                    status = outcome_text(body)
                    current = "实际结果 · " + action_name(step) + "（" + str(status) + "）"
                    reason = reason_text(plan) if plan else reason
                    inner = body.get("result") if isinstance(body.get("result"), dict) else body
                    if isinstance(step, str) and step.startswith("declare-war-"):
                        wars = inner.get("active_wars", [])
                        target_id = plan.get("declaration", {}).get("target_character_id")
                        matched = [war for war in wars if isinstance(war, dict)
                                   and war.get("primary_opponent_character_id") == target_id
                                   and war.get("player_side") == "attacker"
                                   and war.get("targeted_title_ids") == plan.get("declaration", {}).get("target_title_ids")]
                        war_decision = "向" + targets.get(target_id, f"角色 #{target_id}") + "宣战"
                        if len(matched) == 1 and inner.get("accepted") is True:
                            war_decision += f" · 已读回战争 #{matched[0].get('war_id')}"
                        else:
                            war_decision += " · 战争结果未确认"
                        war_decision += "\n理由：" + war_reason(plan)
                    if (step == "query-army-strengths-v1" and isinstance(inner.get("army_strengths"), list)
                            and inner.get("accepted") is not False and body.get("status") == "executed"):
                        blocker = ""
                    records.append(f"{clock} 返回 · {action_name(step)} · {status}")
                records[:] = records[-8:]
                seen.add(path.name)
            pending = [p for p in (session / "requests").glob("*.json") if not (session / "responses" / p.name).exists()]
            pending_text = ""
            if pending:
                item = json.loads(sorted(pending)[-1].read_text(encoding="utf-8"))
                pending_text = "\n请求处理中：" + item.get("tool", "") + "（结果尚未确认）"
            content = "本局：" + args.campaign_label + "\n" + current + pending_text
            if blocker:
                content += "\n未解决阻点：军力读取超限，尚未取得成功回执。"
            if war_decision:
                content += "\n\n宣战决定与实际回执\n" + war_decision
            content += "\n\n当前理由\n" + (reason or "尚无新的决策理由")
            content += "\n\n最近记录（计划与结果分开）\n" + "\n".join(records[-3:])
            content += "\n\n数据来自本局实际请求与回执；请求返回不等于战斗获胜。"
            if content != last_render:
                window.update(content)
                last_render = content
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            window.update("回执读取暂不可用：" + type(error).__name__, "实时决策 · 数据暂不可用")

    receipt = {"session": str(session), "game_pid": launch["pid"], "overlay_hwnd": hwnd,
               "game_creation_filetime": times[0].value, "overlay_pid": os.getpid(),
               "at_utc": datetime.now(timezone.utc).isoformat(),
               "observed_extended_style": get_style(hwnd, -20),
               "foreground_before": foreground_before, "foreground_after": user.GetForegroundWindow(),
               "gameplay_input": False, "target_labels": targets,
               "campaign_label": args.campaign_label,
               "data_source": "actual requests/responses; no simulated decisions"}
    with (session / f"ROOT-DECISION-OVERLAY-{os.getpid()}-STARTED.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    try:
        tick()
        window.run(tick)
    finally:
        kernel.CloseHandle(handle)
        with (session / f"ROOT-DECISION-OVERLAY-{os.getpid()}-CLOSED.json").open("x", encoding="utf-8") as f:
            json.dump({"at_utc": datetime.now(timezone.utc).isoformat(), "game_pid": launch["pid"]}, f)


if __name__ == "__main__":
    main()
