"""Show actual Root file-queue plans, submissions and outcomes over the game."""
from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from decision_overlay_window import NativeOverlay


def outcome_text(body):
    inner = body.get("result") if isinstance(body.get("result"), dict) else body
    if inner.get("checkpoint", {}).get("status") == "saved":
        return "存档文件已确认"
    status = inner.get("status", body.get("status", ""))
    return {"submitted": "已提交，等待读回", "executed": "本步骤已返回",
            "available": "查询已返回", "enacted": "已读回施行结果",
            "centered": "镜头位置已读回", "already_centered": "镜头已在目标处",
            "blocked": "受阻", "rejected": "已拒绝"}.get(status, status or "已返回")


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
    return reasons.get(phase, plan.get("reason") or "等待实际决策理由。")


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--launch-receipt", type=Path,
                        help="Exact launch receipt when continuing this session after a process restart")
    parser.add_argument("--campaign-label", default="当前自动游玩局")
    parser.add_argument("--target-label", action="append", default=[], metavar="ID=NAME")
    parser.add_argument("--desktop-id", help="Exact managed Desktop1 GUID; reject a different Game desktop")
    parser.add_argument("--decision-text-file", type=Path,
                        help="New small file below session, written atomically for a dedicated OBS text source")
    args = parser.parse_args()
    session = args.session.resolve()
    launch_path = args.launch_receipt or session / "ROOT-ACTUAL-GAME-LAUNCH.json"
    launch = json.loads(launch_path.read_text(encoding="utf-8"))
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
    date = launch["creation_date"]
    expected = datetime.strptime(date[:21], "%Y%m%d%H%M%S.%f").replace(
        tzinfo=timezone(timedelta(minutes=int(date[21:]))))
    if abs(created - expected.timestamp()) > .001:
        kernel.CloseHandle(handle)
        raise RuntimeError("Game process generation differs from the launch receipt")
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.restype = ctypes.c_void_p
    foreground_before = user.GetForegroundWindow()
    held = [handle]
    def release_game_handle():
        if held[0]:
            kernel.CloseHandle(held[0])
            held[0] = None
    atexit.register(release_game_handle)
    import win32gui
    import win32process
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ck3_autonomous_player" / "src"))
    from xar_autoplayer.bridge.windows_virtual_desktop import window_virtual_desktop, move_own_window_to_desktop
    game_windows = []
    def collect_game_window(game_hwnd, _extra):
        if (win32gui.IsWindowVisible(game_hwnd)
                and win32process.GetWindowThreadProcessId(game_hwnd)[1] == launch["pid"]
                and win32gui.GetWindowText(game_hwnd) == "Crusader Kings III"):
            game_windows.append(game_hwnd)
    win32gui.EnumWindows(collect_game_window, None)
    if len(game_windows) != 1:
        raise RuntimeError("overlay requires one exact owned Game window")
    game_hwnd = game_windows[0]
    game_desktop = window_virtual_desktop(game_hwnd)
    import uuid
    desktop_id = str(uuid.UUID(args.desktop_id or game_desktop["desktop_id"]))
    if game_desktop["desktop_id"] != desktop_id:
        raise RuntimeError("Game has not reached the managed desktop")
    decision_text = args.decision_text_file.resolve() if args.decision_text_file else None
    def publish_decision_text(content):
        if not decision_text:
            return
        payload = ("进程绑定：PID " + str(launch["pid"]) + " · " + date
                   + "\n面板含本局最后已知回执；不将历史回执计为本次新动作。\n" + content).encode("utf-8")
        if len(payload) > 32768:
            raise ValueError("decision text exceeded its finite byte limit")
        temporary = decision_text.with_name(decision_text.name + f".{os.getpid()}.{uuid.uuid4().hex}.pending")
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
            os.replace(temporary, decision_text)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    if decision_text:
        if not decision_text.is_relative_to(session) or decision_text.exists():
            raise ValueError("decision text must be a new file below this session")
        with decision_text.open("x", encoding="utf-8") as stream:
            stream.write("进程绑定：PID " + str(launch["pid"]) + " · " + date
                         + "\n等待本次进程的真实回执；未确认新行动。\n")
    window = NativeOverlay()
    atexit.register(window.close)
    hwnd = window.hwnd
    overlay_desktop = move_own_window_to_desktop(hwnd, str(game_desktop["desktop_id"]))
    window.set_content_visible(overlay_desktop["desktop_id"] == desktop_id
                               and not win32gui.IsIconic(game_hwnd))
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
    camera_text = ""
    def close_panel(message):
        try:
            publish_decision_text(message + "此前内容仅为最后已知回执。")
        finally:
            window.set_content_visible(False)
            window.destroy()

    def tick():
        nonlocal war_decision, current, reason, last_render, blocker, camera_text, game_desktop, overlay_desktop
        process_state = kernel.WaitForSingleObject(handle, 0)
        if process_state == 0 or (session / "STOP-DECISION-OVERLAY").exists():
            close_panel("面板已停止：游戏已退出或 owner 已请求停止。")
            return
        if process_state != 258:
            close_panel("面板已停止：游戏内核状态未知。")
            return
        try:
            if (not win32gui.IsWindow(game_hwnd)
                    or win32process.GetWindowThreadProcessId(game_hwnd)[1] != launch["pid"]):
                close_panel("面板已停止：原游戏窗口已失效。")
                return
            observed_game_desktop = window_virtual_desktop(game_hwnd)
            if observed_game_desktop["desktop_id"] != desktop_id:
                close_panel("面板已停止：游戏离开固定管理桌面。")
                return
            overlay_desktop = window_virtual_desktop(hwnd)
            if overlay_desktop["desktop_id"] != desktop_id:
                window.set_content_visible(False)
                overlay_desktop = move_own_window_to_desktop(hwnd, desktop_id)
            window.set_content_visible(overlay_desktop["desktop_id"] == desktop_id
                                       and not win32gui.IsIconic(game_hwnd))
            for path in sorted((session / "responses").glob("*.json")):
                if path.name in seen:
                    continue
                if path.stat().st_size > 16 * 1024 * 1024:
                    summary_path = session / "display-responses" / path.name
                    if summary_path.exists() and summary_path.stat().st_size <= 128 * 1024:
                        row = json.loads(summary_path.read_text(encoding="utf-8"))
                    else:
                        current = "回执过大，等待实际 SDK 摘要；原件保留"
                        break
                else:
                    row = json.loads(path.read_text(encoding="utf-8"))
                result, body = decode(row)
                plan = body.get("plan") if isinstance(body.get("plan"), dict) else {}
                step = body.get("selected_step") or body.get("step") or plan.get("selected_step")
                tool = row.get("request", {}).get("tool") or row.get("tool", "")
                camera = body.get("camera_follow")
                if isinstance(camera, dict):
                    camera_text = "镜头跟随：" + outcome_text(camera)
                    hotspot = camera.get("hotspot")
                    if isinstance(hotspot, dict):
                        camera_text += " · " + str(hotspot.get("title_key", hotspot.get("province_id", "")))
                    if camera.get("status") == "unavailable":
                        camera_text += "（本轮未确认）"
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
                elif tool == "root_before_auto_turn_submit":
                    if body.get("status") == "planned" and plan:
                        current = "提交前计划 · " + action_name(step)
                        reason = war_reason(plan)
                        records.append(f"{clock} 提交前计划 · {action_name(step)}")
                    else:
                        current = "提交前计划不可用"
                        reason = "Root 提交前记录缺少 planned 状态或实际 plan；未确认任何动作结果。"
                        records.append(f"{clock} 提交前记录不可用")
                elif tool == "ck3_plan_turn":
                    current = "计划中 · " + action_name(step)
                    reason = war_reason(plan)
                    records.append(f"{clock} 计划 · {action_name(step)}")
                elif tool == "ck3_auto_turn" or step:
                    status = outcome_text(body)
                    current = "实际结果 · " + action_name(step) + "（" + str(status) + "）"
                    reason = war_reason(plan) if plan else reason
                    inner = body.get("result") if isinstance(body.get("result"), dict) else body
                    if isinstance(step, str) and step.startswith("declare-war-"):
                        wars = inner.get("active_wars", [])
                        target_id = plan.get("declaration", {}).get("target_character_id")
                        title_ids = plan.get("declaration", {}).get("target_title_ids")
                        matched = [war for war in wars if isinstance(war, dict)
                                   and war.get("primary_opponent_character_id") == target_id
                                   and war.get("player_side") == "attacker"
                                   and war.get("targeted_title_ids") == title_ids
                                   and type(war.get("war_id")) is int and war["war_id"] > 0]
                        war_decision = "向" + targets.get(target_id, f"角色 #{target_id}") + "宣战"
                        if (type(target_id) is int and isinstance(title_ids, list) and title_ids
                                and all(type(value) is int for value in title_ids)
                                and len(matched) == 1 and inner.get("accepted") is True):
                            war_decision += f" · 已读回战争 #{matched[0].get('war_id')}"
                        else:
                            war_decision += " · 战争结果未确认"
                        war_decision += "\n理由：" + war_reason(plan)
                    army_rows = inner.get("army_strengths", inner.get("armies"))
                    if (step == "query-army-strengths-v1" and isinstance(army_rows, list)
                            and inner.get("accepted") is True and body.get("status") == "executed"):
                        blocker = ""
                        current += "\n军队兵力：" + "；".join(
                            f"#{army.get('army_id')}：{army.get('current_soldiers')} 人"
                            for army in army_rows[:6] if isinstance(army, dict))
                    records.append(f"{clock} 返回 · {action_name(step)} · {status}")
                records[:] = records[-8:]
                seen.add(path.name)
            pending = [p for p in (session / "requests").glob("*.json") if not (session / "responses" / p.name).exists()]
            pending_text = ""
            if pending:
                item = json.loads(sorted(pending)[-1].read_text(encoding="utf-8"))
                pending_text = "\n请求处理中：" + item.get("tool", "") + "（结果尚未确认）"
            content = "本局：" + args.campaign_label + "\n" + current + pending_text
            if camera_text:
                content += "\n" + camera_text
            if blocker:
                content += "\n未解决阻点：军力读取超限，尚未取得成功回执。"
            if war_decision:
                content += "\n\n宣战决定与实际回执\n" + war_decision
            content += "\n\n当前理由\n" + (reason or "尚无新的决策理由")
            content += "\n\n最近记录（计划与结果分开）\n" + "\n".join(records[-3:])
            content += "\n\n数据来自本局实际请求与回执；请求返回不等于战斗获胜。"
            if content != last_render:
                window.update(content)
                publish_decision_text(content)
                last_render = content
        except Exception as error:
            window.set_content_visible(False)
            try:
                publish_decision_text("决策数据暂不可用：" + type(error).__name__
                                      + "。此前内容仅为最后已知回执，未确认新的成功动作。")
            except OSError:
                window.destroy()
                return
            last_render = None
            window.update("回执读取暂不可用：" + type(error).__name__, "实时决策 · 数据暂不可用")

    self_handle = kernel.OpenProcess(0x00101000, False, os.getpid())
    self_times = [ctypes.c_uint64() for _ in range(4)]
    try:
        if not self_handle or not kernel.GetProcessTimes(self_handle, *(ctypes.byref(v) for v in self_times)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if self_handle:
            kernel.CloseHandle(self_handle)
    receipt = {"session": str(session), "game_pid": launch["pid"], "overlay_hwnd": hwnd,
               "game_creation_filetime": times[0].value, "overlay_pid": os.getpid(),
               "overlay_creation_filetime": self_times[0].value, "overlay_executable": str(Path(sys.executable).resolve()),
               "launch_receipt": str(launch_path),
               "game_hwnd": game_hwnd, "game_virtual_desktop": game_desktop,
               "overlay_virtual_desktop": overlay_desktop,
               "at_utc": datetime.now(timezone.utc).isoformat(),
               "observed_extended_style": get_style(hwnd, -20),
               "foreground_before": foreground_before, "foreground_after": user.GetForegroundWindow(),
               "gameplay_input": False, "target_labels": targets,
               "campaign_label": args.campaign_label,
               "managed_desktop_id": desktop_id, "hidden_desktop_content_enabled": True,
               "decision_text_file": str(decision_text) if decision_text else None,
               "data_source": "actual requests/responses; no simulated decisions"}
    with (session / f"ROOT-DECISION-OVERLAY-{os.getpid()}-STARTED.json").open("x", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(json.dumps(receipt, ensure_ascii=False), flush=True)
    try:
        tick()
        window.run(tick)
    finally:
        try:
            publish_decision_text("面板 owner 已结束。此前内容仅为最后已知回执，未确认新的成功动作。")
        finally:
            window.close()
            release_game_handle()
        with (session / f"ROOT-DECISION-OVERLAY-{os.getpid()}-CLOSED.json").open("x", encoding="utf-8") as f:
            json.dump({"at_utc": datetime.now(timezone.utc).isoformat(), "game_pid": launch["pid"]}, f)


if __name__ == "__main__":
    main()
