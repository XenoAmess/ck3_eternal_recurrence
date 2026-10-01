# R0134 后态 control 拒绝与最小修正

R0134 仅完成前态原图与战线宽度同暂停读数。日期已经实际推进一次：raw53146488 → 53146512，后态 snapshot 为 paused=true、actor29829、public revision8/native7。后态 UI 样本为 0，不能称前后同帧补证完成。

`mcp-calls.jsonl` 第405行明确返回 `experimental trace permits only exact-day timeline controls and finish`。190 源 `bridge.cpp:10465–10476` 在实验 trace 仍 armed 时，先拒绝其余 execute_step。该回件没有 battle_control body/status；driver_state 缓存旧 control 不是后态读数。本轮 trace-finish 请求和回件均不存在，不能借旧 attempt 的 failed/1040 状态描述本轮。

旧 consumer 的 probe_after 先调用包含 snapshot+control 的 paused()，然后才 finish。新 consumer 仅把前置 probe 改为严格 +24 paused actor/war/army snapshot；用其当前 public revision finish 一次；再由原 sample(after) 取得 fresh snapshot/control、真实原图/tooltip，最后继续原 after-pixels same_paused_frame。日期、trace token、control、UI、清理 guards 保留。finish 回件失败或模糊只读取已保全回件，不重发；若未释放或 controlled stop，fresh control 按原 guard 拒绝，保留缺口并清理。

190 / ED537 DLL、旧 attempt24 及本次 run 原件未修改。11 条纯离线控制流检查及4条实际绑定/help入口 probe 通过，独立窄审另有16条 AST 条件通过；新实机未启动。冻结见 variant-freeze.json，入口见 ready-report-a01.json。完整下方面板不足仍是独立缺口。
