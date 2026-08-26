# XAR Autoplayer MCP Bridge（数据 Mod 原型）

这是只给自动游玩 profile 挂载的独立开发 Mod，不属于琉焰卿主 Mod，也不进入 Workshop 发布构建。它验证最低成本的双向闭环：外部伴随进程写 CK3 用户目录下的 `run/xar_mcp_inbox.txt`，隐藏 GUI 约每 `0.4` 秒执行一次该文件，白名单 scripted effect 再把结构化 snapshot 与 ACK 写入 `debug.log`。

## 已实现的最小协议

默认 inbox 模板是纯注释 no-op。伴随进程需要先把 [templates/xar_mcp_inbox.txt](templates/xar_mcp_inbox.txt) 复制到当前 CK3 userdir 的 `run/xar_mcp_inbox.txt`。请求 snapshot 时，用临时文件原子替换为：

```text
xar_mcp_take_snapshot = { REQUEST_ID = xar_req_000001 }
```

`REQUEST_ID` 是 CK3 flag token，只使用 ASCII 字母、数字和下划线。桥会在 `debug.log` 产生基础状态，并额外投影琉焰卿主 Mod 已提交的一代制死亡结算：

```text
XAR_MCP:BEGIN|schema=1|kind=snapshot|request_id=xar_req_000001
XAR_MCP:STATE|player_id=4294967297|date=15 September, 1067|total_days=389742
XAR_MCP:SETTLEMENT|ready=1|commit_serial=1|source_character_id=4294967297|final_score=284.625|score_before_reject=287.500|record_candidate=284|old_record=250|record_delta=34|blessing_count=7|refusal_count=1|contract_progress=9|record_written=1
XAR_MCP:ACK|schema=1|request_id=xar_req_000001|command=take_snapshot|status=ok
XAR_MCP:END|schema=1|request_id=xar_req_000001
```

未结算时该行是 `XAR_MCP:SETTLEMENT|ready=0|commit_serial=0`；没有 `SETTLEMENT` 行的旧版四行 frame 仍可解析，其 `one_life_settlement` 为 `null`。只有完整的 `BEGIN -> STATE -> ACK -> END` 才算成功，可选投影必须位于该 frame 内。Data Mod driver 将完整 payload 归一为 `one_life_settlement`，并通过 `game.state.xar-one-life-settlement` capability 声明该字段。

检测到 ACK 后立即把 inbox 原子替换回 no-op；在替换生效前，同一个只读请求可能被 0.4 秒轮询重复执行，伴随进程按 `request_id` 去重即可。当前 effect 只读取 `GetPlayer`、当前日期、total days 和主 Mod 已提交的 save-scoped `xa_settlement_*` globals，不修改游戏状态，也没有任何 CK3 AI 入口。

## 为什么这样挂 GUI

`gui/scripted_widgets/xar_mcp_bridge_widgets.txt` 让 CK3 启动时创建不可见顶层窗口。其 counter widget 复用了 Voices of the Court 的已公开模式：一个 state 调 `ExecuteConsoleCommand('run xar_mcp_inbox.txt')`，另一个 state 等待 0.4 秒后用 `gui.createwidget` 重建 counter。原版 `gui/console.gui` 也直接使用 `ExecuteConsoleCommand('run run.txt')`，而 `GetPlayer.GetID`、`GetCurrentDate.GetStringShort`、`GetCurrentDate.GetDateAsTotalDays` 的日志插值来自 VOTC 公开 effect。

2026-08-26 的 owner-subset retreat v13 managed artifact 已在 CK3 1.19.0.6 实证这条链：non-debug、暂停、
读档完成后，counter 每 `0.4s` 持续执行 `run`，并会重新读取原子替换后的文件。换人后与清理 guard 后各连续取得
两个不同 request ID 的完整 snapshot frame，四帧均为同一玩家与日期；artifact SHA-256 为
`7780B619B2E7B90B8D5D5030D779F58F266585A6246A79B6C2FE20EF0F2701F9`。这证明 paused poll transport，
不把临时 data Mod 当成 production gameplay action。

## 安装到一次性 autoplayer profile

1. 把本目录作为独立 Mod 加入专用播放集；不要合并进主 Mod。
2. 把 no-op 模板复制到该 profile 的 `run/xar_mcp_inbox.txt`。
3. 启动伴随进程，让它只写已定义的 typed effect 调用。
4. 从该 profile 的 `logs/debug.log` 增量解析 `XAR_MCP:` 帧。

本目录没有外层 `.mod`，因为 profile 的绝对路径注册文件必须由环境准备器按实际 userdir 生成。`descriptor.mod` 不含 `remote_file_id`。

## 静态验证

```powershell
py -m unittest discover -s ck3_autonomous_player/mod_bridge/tests -p "test_*.py"
```

测试覆盖 BOM、widget 注册与 0.4 秒循环、typed effect 字段、no-op inbox、旧四行 frame 兼容，以及完整/未发布/损坏结算投影的解析。静态通过仍不能替代上述 exact-build managed artifact。
