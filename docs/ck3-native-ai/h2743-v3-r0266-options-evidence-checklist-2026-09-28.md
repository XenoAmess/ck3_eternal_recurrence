# H2743 v3 同帧终战选项取证清单（供 R0266）

状态：**静态计划，尚未占屏或运行本轮实机**。H2743 `attempt-02` 曾在原 DLL `8C3A…8A5C` 下证明投降合法且会被接受；那份旧 payload SHA `D7C6A50F5120944B4C53C42B52D0C64734BE9B169235F1C5764B3AABEA0DD2EB` 不能代替只读 V1 候选 DLL `FD8B…1470` 的同次查询，也不能给 R0266 填即时费用。

| 门 | 本次同一新 attempt 必须保存的内容 | 缺失时结论 |
| --- | --- | --- |
| 输入与装载 | H2743 原 save `A501…10E9`、driver `F314…B150`、family `12D7…5724`、源 DLL 身份 `8C3A…8A5C`；当前运行候选 DLL `6689…B17E`（旧 `FD8B…1470` 仅为历史旧请求）、injector `C89F…84FF`、EXE `2D00…DB86` 的完整 SHA/大小/绝对路径。`ready-summary.json`、派生 driver 前哈希、启动 argv、会话 ready PID、实际 CK3 EXE 路径，以及进程模块列表的 loaded DLL 路径与当前磁盘文件 SHA；模块不能证实时明确 RED，不得把 argv 当已装载事实或宣称内存映像 SHA。 | 路径／当前磁盘身份不完整；R0266 不能消费 fee 证据。 |
| 环境 | 本机唯一 `ck3-screen:acquired`、当次新鲜 Steam 位移截图与人工“离线模式”审阅、全新 no-launch 配对；冷启动租约 heartbeat 与外置 append-only attempt。 | 不启动或保留 RED。 |
| 同帧查询 | `ck3_take_snapshot` 精确 paused H2743；同一 MCP 会话保存 `ck3_execute_step` 的**原样请求** `{"step":"query-war-termination-options-16777231"}` 和原样 envelope/payload，各自 SHA、`query_sequence`、`queried_snapshot_id`、`queried_revision`、`queried_native_revision`、`queried_connection_generation`、`termination_query_context`，再保存 V1 de-jure baseline 双读及查询后 snapshot。前后 WarID `16777231`、Robert `29829`、Landolf `30097`、CB index `17`、目标 `[2128]`、date_raw `53217264`、native revision 必须相同。 | 旧帧或另一次会话不能合并；fee 仍 unknown。 |
| 无动作与清理 | 唯一额外 `execute_step` 为 `query-war-termination-options-16777231`；无日期推进、投降、白和平、移动、预览。保留 CK3 managed stop 回执：supervisor 0、CK3 PID 空、stdout reader 停止；源四件、候选 DLL/injector、已放置 save/sidecar 后哈希；将 `session-exit.json` SHA 绑定最终只读结果。 | 原始查询可留作 RED 诊断，不能写最终成功或现金事实。 |

2026-09-28 更新：#448 的 `run_h2743_dejure_readonly_v3.py` 已静态实现同一 MCP 暂停会话内的 V1 双读（现要求 Title `2128` 的 typed holder/个人领主前态）、一次终战选项只读查询、各次原始 request/envelope/payload、六字段前后同帧、完整 active-war 签名对照、运行中 CK3 EXE 与已装载 DLL 模块路径和**当前磁盘文件** SHA 回读，以及退出后的清理与输入后哈希门。模块 audit 不证明内存映像 bytes。`--check-static` 还检查当前解释器可读取自身模块映射。此处只说明代码已实现；尚无新 H2743 no-launch/live 证据，不能把旧 `attempt-02` 拼接进新 run。该直接查询不含正式选择器的 `selected_step` 与 typed `priced_command`，所以 R0266 的费用审批仍为空，也不能推定投降总资源 delta 为零或解禁 H2743 退出动作。屏幕队列继续由主任务协调。
