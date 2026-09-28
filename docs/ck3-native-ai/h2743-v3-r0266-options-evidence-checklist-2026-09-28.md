# H2743 v3 同帧终战选项取证清单（供 R0266）

状态：**静态计划，尚未占屏或运行本轮实机**。H2743 `attempt-02` 曾在原 DLL `8C3A…8A5C` 下证明投降合法且会被接受；那份旧 payload SHA `D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB` 不能代替只读 V1 候选 DLL `FD8B…1470` 的同次查询，也不能给 R0266 填即时费用。

| 门 | 本次同一新 attempt 必须保存的内容 | 缺失时结论 |
| --- | --- | --- |
| 输入与装载 | H2743 原 save `A501…10E9`、driver `F314…B150`、family `12D7…5724`、源 DLL 身份 `8C3A…8A5C`；运行候选 DLL `FD8B…1470`、injector `C89F…84FF`、EXE `2D00…DB86` 的完整 SHA/大小/绝对路径。`ready-summary.json`、派生 driver 前哈希、启动 argv、会话 ready PID、实际 CK3 EXE 路径，以及若原生进程模块列表可审计则实际 loaded DLL 路径与文件 SHA；模块不能证实时明确 `loaded_dll_unavailable`，不得把 argv 当已装载事实。 | binary identity 不完整；R0266 不能消费 fee 证据。 |
| 环境 | 本机唯一 `ck3-screen:acquired`、当次新鲜 Steam 位移截图与人工“离线模式”审阅、全新 no-launch 配对；冷启动租约 heartbeat 与外置 append-only attempt。 | 不启动或保留 RED。 |
| 同帧查询 | `ck3_take_snapshot` 精确 paused H2743；同一 MCP 会话保存 `ck3_execute_step` 的**原样请求** `{"step":"query-war-termination-options-16777231"}` 和原样 envelope/payload，各自 SHA、`query_sequence`、`queried_snapshot_id`、`queried_revision`、`queried_native_revision`、`queried_connection_generation`、`termination_query_context`，再保存 V1 de-jure baseline 双读及查询后 snapshot。前后 WarID `16777231`、Robert `29829`、Landolf `30097`、CB index `17`、目标 `[2128]`、date_raw `53217264`、native revision 必须相同。 | 旧帧或另一次会话不能合并；fee 仍 unknown。 |
| 无动作与清理 | 唯一额外 `execute_step` 为 `query-war-termination-options-16777231`；无日期推进、投降、白和平、移动、预览。保留 CK3 managed stop 回执：supervisor 0、CK3 PID 空、stdout reader 停止；源四件、候选 DLL/injector、已放置 save/sidecar 后哈希；将 `session-exit.json` SHA 绑定最终只读结果。 | 原始查询可留作 RED 诊断，不能写最终成功或现金事实。 |

当前 #448 的 `run_h2743_dejure_readonly_v3.py` 只执行 `query-defender-de-jure-exit-terms-v1-16777231` 双读；**尚未自动调用并保全上述终战选项 query，也没有实际进程模块装载回执**。获屏前应先完成该同会话只读扩展的审阅，或用受控辅助 MCP 调用且满足同一 session/frame 与清理门；不能临场把另一个 run 的选项结果拼接。R0266 只能审核选项读口在精确帧对 immediate fee 的可见边界；即使其条件性判断为零，也不能推定投降总资源 delta 为零，不能解禁 H2743 退出动作。屏幕队列继续 E2-05 → E2-04 a02 → 本机 H2743，除非来源机先返回可校验的 WAR ACK/结果。
