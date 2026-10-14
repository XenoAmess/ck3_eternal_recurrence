# P11 同 Game 续行与录制监护

2026-10-15 交接；证据时间使用 UTC。以下是 Z 执行机器的实际路径，不是其他机器的目录协议。

外置场次根 `N = D:/codex-ck3-demos/2026-10-14-robert-30year/continuation38-cold-prep`；交付包 `C = D:/codex-ck3-demos/2026-10-14-robert-30year/recording-recovery-p11-01`。P11 只轮换 SDK，继续同一 Game PID 202692、overlay 与录制段 `19730a3a-d565-4a9b-99d0-61f672f2a8a0`。

## 冻结输入与失败来源

| N 下原件 | SHA-256 |
| --- | --- |
| `root_p11_sdk_queue.py` | `205be84eb6dc147c44edae13819ffe9eb86f376e154529fd181172cab614be37` |
| `root_p11_mcp_entry.py` | `102e8d3aafa2665b00fb77610fd97e643f5cc03a90cb4cec36f3dfa9ba6e8891` |
| `ROOT-P11-SDK-FREEZE.json` | `ecf0ca41cc1da935eb9fa66ab27018a1735672bfdafb555b72e263ac148eb9a9` |
| `ROOT-P11-CUMULATIVE-SEED.json` | `eb73fa4e0136b38504c5dbad6fb5e8857c8907f6aeeabb81a81f200d97239a7a` |

SDK 精确树为 `N/sdk-p11/src`，1288 文件；NativeDriver 为已审 SHA `17c278c4dfc215e3466a5c235408867aceaacd9ef7751e91b2d174d9ee25cdd7`。结果分类器使用 `D:/codex-ck3-demos/2026-10-14-robert-30year/p08-popup-pause-final04/root_cold_result_classifier.py`，SHA `fc06540b5ce6281d9889a3920b720248f2c4cd6ac9d6b599387dfa92a3d50c03`。新仓库提交不会自动改变这些活跃冻结输入。

原 P08 AUTO139 在推进后遇到暂停错误，其结果未知；原件 `N/p08-responses/0139-1-result.json` 保留。1749 未结算分支在新 seed 中放弃，业务计数不增加、不重放 AUTO。启动锚点取实际 P10 只读 SEM1 的 actor/episode/date（53171472）与 event11，保留原 1748 已结算周期。

P09 在任何工具调用前正常关闭。P10 的只读 SEM1 已返回，但旧 `root_warm_overlay_relay.py` 将所有轮换写到 `responses/cold38-0001-1-result.json`，撞上 P08 原件；此错误不能当作 Game 或录制失败。旧 publisher 还读取共享 `CURRENT-REQUEST.json` 并写无前缀 plan，P11 一并修正这两处。P09/P10 原输入、响应与关闭回执没有覆盖。

## 实机完成与边界

`N/p11-responses/0004-1-result.json`：实际 `ck3_execute_step("pause-map", expected_revision=当前 SEM revision)` accepted。`0005-1-result.json` 独立读回 `paused=True`、同 actor/episode/date，事件仍为11；暂停 ACK 本身没有替代后验。

`0006-1-result.json` 为 Root 首个 full1，实际完成至1749。Root 的 feeder 随后从已完成控制6继续控制9 full30，没有重发控制6。`0014-1-result.json` 实际选择 `select-event-option-1`，原事件11后验为 `event_instance_advanced`、`postcondition_verified=True`、新实例 `None`；该原件 SHA `bcec0a36c64c1d362db3b90b66680c5b6e3716f05acf66ca0c011c6d84bdcd98`。

Root 实际通过 `C/live-watchdog01` 使用 `--start` 启动监护；该目录的 `LAUNCH-REQUEST.json` 记录 redirector PID220068，仅此 PID 不证明运行健康。实际 `N/automatic-recording-recovery-p11/STATUS.json` 在 `2026-10-14T21:20:49.569925Z` 为 `idle / healthy`、无 recovery/error。这个可变文件的当时原始字节另存为 `D:/codex-ck3-demos/2026-10-14-robert-30year/permanent-recording-continuity01/P11-WATCHDOG-HEALTHY-OBSERVED.json`，SHA `5b0e31019b96b9449293189fa712843cbf4a0edb4306ff4a3a06d23b8a3c96bb`。

这证明监护实际启动并完成健康观察，**没有验收新的故障恢复分支**。本轮没有故意停止 overlay/OBS、制造录制失败或操作 Game 来测试恢复。自动恢复仍只接收既有精确 `RecordingPaused + full_loop + auto_verified + 原动作未重放` 合同；未知业务结果继续保留，不能宣称可自动恢复任意 gameplay 错误。

## 永久可复用部分

`tools/g2_saved_campaign/recording_recovery_adapter.py` 与 launcher 接入显式 `--feeder-stop-marker`；launcher 也转发 `--attach-only` 并如实记入计划，默认行为保持。`decision_observation_feed.py` 将实际结果按源目录命名共享 feed，并让 pre-submit publisher 使用调用方的确切当前请求与响应目录；原件占名时明确失败，不覆盖或重放。

8 项新增 portable pytest 通过，覆盖 CLI 默认 dry-run/参数传递、默认与自定义 STOP、跨前缀结果、真实 callback 的上下文、原件与竞争写入保护；仅使用合成小夹具。P11 外置完整最终 queue.call / 真实外层 reinforcement / 真实 relay 与 publisher 的4项离线回归也通过。完整场次 queue 和专用策略不整份入库；以后轮换应使用新的输出前缀并审阅全部 sidecar 调用方。

原件时效与容量按通用存储策略1.0.0复核。当前活跃 SDK/seed/profile/录像和最小未解决失败证据仍有用途；测试派生物闭场后48小时可评估回收，原始证据默认30天、超过1GiB七天内提前复核。上述历史 SHA 不替代原件现有可读性；本次没有执行删除。
