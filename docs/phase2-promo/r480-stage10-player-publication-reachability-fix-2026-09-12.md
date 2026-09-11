# R480 后 Stage 10 玩家公示可达性修复

## 结论

T0-P1 仍为 **`8/9 = 88.9%`**，唯一未签收项仍是玩家可见的 `zg361mg.120`。本包确认并修复了一个真实 mod 可达性缺陷：B1 改成玩家限定后，Stage10 仍要求 AI 直属经理拥有自己的旧 `zg361_review_serial`，而该 serial 已没有正式生产者。R467 的 `no_bounded_ai_direct_manager` 因此不是单纯缺少合适存档，而是旧入口与当前玩家限定合同不一致的实机信号。

修复已完成静态验收，尚未取得新实机 terminal，所以 `.120` RED 仍保留，P1 尚未签收，P2 最终宣传视频继续硬锁定。本包没有检查、更新、制作或发布视频物料。

## 根因与最小修复

旧链要求 `subject.review_serial < owner.review_serial`。提交 `380af02c8ccaace03144c6ea2beb4dda32454a33` 为落实玩家限定，停止了 AI 年度 B1，但 Manager/Governance 的 dispatcher、F/AK opener 与 case kernel binding 仍读取上级/AI 的旧 serial。正常单人局中，玩家作为最高 owner 时只能枚举没有 serial 的 AI 经理；玩家作为下级经理时，其 AI 上级又没有 serial，两个方向都不能新开玩家 `.120`。

当前修复保留玩家限定，不恢复 AI 年度 pulse 或后台 decision：

1. 玩家经理完成真实 B1 公示时，`zg361_p2c_on_review_published_effect` 调用 `zg361_mg_schedule_player_manager_assessment_effect`。
2. 调度器要求当前 subject `is_ai = no`、天朝制、公爵及以上、有真实 `zg361_review_serial` 且直属上级合格；同一公示 serial 只调度一次。
3. 隐藏事件 `zg361mg.90` 在 D+1 把 ROOT 重置为直属上级，仅用于保留 F/AK 的 `owner = direct superior` 身份；随后仍在玩家 subject 上开案。
4. F/AK 使用独立的 owner-local `zg361_mg_evaluation_cycle_serial`。玩家公示回调把它设为 `subject.review_serial + 1`，因此 source 严格早于 evaluation cycle，同时不会伪造上级本人参加过 B1。
5. Stage10 cohort 和公共 opener 都增加 `is_ai = no`。旧存档即使残留 AI `review_serial`，也不能新开 AI 管理案件。

## 定向验证

- `test_zg361_case_kernel.py`：normal / optimized 各 `12/12` GREEN。
- `test_zg361_manager_governance_runtime.py`：normal / optimized 各 `53/53` GREEN；覆盖玩家公示调度、幂等、直属上级重置、独立 evaluation cycle、不得写 owner `review_serial`、AI cohort 拒绝。
- `test_zg361_phase2_central_runtime.py`：normal / optimized 各 `45/45` GREEN；覆盖 publication hook 与 Stage10 玩家闸门。
- 三个生成器 `--check` GREEN；`tools/validate_local.py` GREEN；`git diff --check` GREEN。

旧 `tools/test_zg361_phase2_product_projection.py` 的 canonical-mismatch 用例仍引用已退役的 `common/scripted_effects/zg361_effects.txt`，所以在预期 hash mismatch 前先报 source file missing。这是现有测试夹具漂移，本包没有改它；实际产品树已由 `validate_local.py` 通过。该诊断不替代也不阻断 `.120` 的实机门。

## 下一轮唯一实机动作

当前轮次 R480 已结束，旧轮次 R479 已终止，CK3、injector、Operator MCP 均为零。脚本游戏资产已经变化，不能热恢复；下一次必须启动新轮次 R481。R481 只执行一次有界 Stage10 验收：复用真实玩家经理 B1 lineage，等待真实公示触发 `.90`，在同一进程内取得 `.120`，并回读 F case 的 owner/subject/source/evaluation cycle、终态和 manager RED。成功后立即更新九项账本为 9/9；失败则保存首个 RED 并停止，不延长为单 bug 长跑。

本变更改变 Manager/Governance 的入口架构和周期字段语义，必须在根仓提交推送后立即同步 open_kaishek 兼容说明；公共 MCP schema、DLL、启动参数与加载顺序没有变化。

## 有界 runner 与候选源补充

Stage10 action/operator 已从旧 `.390 + selector + set-player` 编排改为真实玩家经理 B1 公示：先用 campaign-root 确认当前玩家
`非独立 + 公爵及以上 + celestial + zg361_on` 及直属上级，再执行 review-now，最多推进 30 游戏日并停在 `.120`；terminal
provider 必须证明同一 owner/player F case 已闭合。聚焦 action normal/optimized 各 `5/5`、operator 各 `4/4` GREEN。

现有 R159 是独立最高统治者，已离线淘汰且不再启动。当前候选 `autosave.ck3` 为 SAV0101 / 1.19.0.6，SHA-256
`80030146765A960EABAA1E38E90FF88CDEB8FBBBB2442E30E695FDFBFD64687D`；玩家 `37884` 的直属上级为 `61334`，直属有地
封臣为 `[57858, 16817470, 43060]`。离线准入使用仓库外通用 Rakaly 0.8.19，实机启动后仍由通用 campaign-root MCP
重新确认，离线结果不冒充 production-live 证据。该路线只允许一次绝对 30 日验收，失败即保存首个 RED，不重试或延长。
