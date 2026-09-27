# 第 11→12 天增援与战斗边界 092：局部原生追踪 GREEN

适用范围是原版 CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`，原始存档 SHA-256 `3F4B2FDAAE1AA2ED4D94958673DDADF4DCDF4A4F49073594B9AE32E782BB6953`，CombatID `16777218`。实验桥 DLL SHA-256 `22411F45F8B23262FE8752275801959A8EA1EB2310F848D805D8BD606231A5CF`，源码版本 `f3abdd6b12ba5983d0c1d8c38cd674d43f917ccd`。092 的全部原始素材保留在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-active-counter-trace-attempt-092`；仓库中的 [`project_active_join_092.py`](../../ck3_autonomous_player/tools/project_active_join_092.py) 逐文件复验哈希并生成供模拟器使用的 [`ck3_1_19_0_6_episode01_active_join_trace_092.json`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_active_join_trace_092.json)。这是一条**观测样本**，没有把它冒充为整场胜率或下一日完全拟合。

092 的输入冻结文件与发给原生桥的 begin 请求一致：`candidate_joining_army_id=22`，`capture_runtime_join_width=true`，`capture_runtime_join_full_entries=true`。输入冻结 SHA-256 `4597C4AF13CBC0783B4D324E590B63F8435AD36E69E208F4B8D3CAFFBD26125E`，begin 请求 SHA-256 `5D5270594F7765FAD423F2FA3CAB0D0BE1B5BBBFE32A9BDC4060960F803F5951`，trace-finish 原始回包 SHA-256 `FE017E2DE3EFF4A481FBBB14632BCE8981F4487E7CAEF97E7DA589971A02CAC8`。只读摘要 SHA-256 `A1DD3CAB234108C44719E18688463F3FD812DBF709AB50018F43F16FB04AD6A3`，清理回执 SHA-256 `C3DC93EF76F2DDC198E63708DF8360A1A12E5C2EC1C9D7A51C65B04ED6E32C6F`。自动恢复器先取得新桌面帧并以窗口移动验证桌面仍响应，目视复核 Steam 为离线模式；CK3 受控退出码 0，进程树清零。

原生追踪从日期 raw `53146488`、战斗 phase day 7 到 `53146512`、phase day 8，七个边界全部身份校验通过，`failure_flags=0`。玩家 Army 18、owner 29829 在 side 1；对方 side 0 原为 Army `16777221, 16777231, 27`，次日 phase-fire 前变为 `16777221, 16777231, 27, 22`。这直接修正了 [090 的 identity failure](active-combat-day12-trace-attempt-090-2026-09-27.md)：090 的 begin 未携带候选 Army 22。091 曾取得同样的局部成功，但它的 `input-freeze.json` 将两个 capture flag 错记为 false，因此只留作诊断，不作为冻结输入一致的正式配对；092 才满足该条件。

| 原生边界 | Army 22 所属 side | phase day | 基础宽度 | 最终宽度 | 出伤宽度实参 | side 0 / side 1 在战总量 raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 入场前 | `-1`，尚未入场 | 7 | 1645 | 1480 | 未传入 | 160317482 / 89325449 |
| 入场后 | 0 | 7 | 2467 | 2220 | 未传入 | 410690163 / 82785368 |
| 次日出伤 | 0 | 8 | 2467 | 2220 | 2220 | 410690163 / 82785368 |

Army 22 有 13 个兵团条目，编制基础人数合计 2570；入场后的当前在战人数 raw 为 `256000000`，按这项人数的 `100000` 倍缩放折合 **2560 人**，不是 2.56 亿人，也不等于 2570 的基础编制。入场前 side 0 的 27 个条目求和为 `154690163`，缓存总量 `160317482`，差 `5627319`；side 1 的 24 个条目求和 `82785368`，缓存 `89325449`，差 `6540081`。入场后 side 0 有 40 个条目，缓存及求和同为 `410690163`；side 1 的 24 个条目缓存及求和同为 `82785368`。因此不能拿入场前缓存 `160317482` 直接减入场后缓存 `410690163`，然后声称差值全是 Army 22；入场前两个缓存尚有与条目求和不一致的残量。

同一受控追踪还取得局部原生数值：反制后、伤害缩放前攻击 raw，side 0 为 `7163402981`、side 1 为 `1455075113`；主 tick 伤亡前出伤 raw，side 0 为 `116118762`、side 1 为 `67660992`，比例均为 `100000`。这些数值可用作拟合的边界约束，但**不能**从它们直接推出各兵团死人、撤退或战斗终局。桥报告 `bounded_capture_complete=true`，同时 `full_mutable_transition_bundle_complete=false`、`original_trace_ready=false`；主动续算输入仍缺反制类别堆栈、下一日非骰子优势来源、骑士参与及动态入场完整状态。下一步应补齐这些缺域，使用这份样本对前后状态逐字段校验，再推动游玩智能体整场胜率决策器，不把局部通过上调为整日预测通过。
