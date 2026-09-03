# 天朝二期双宣传片导演方案

这里是天朝二期两条正式宣传片路线的权威导演文档入口。用户已明确要求：**两个版本都保留、都制作、都分别交付成片。**二者不存在“主方案/废案”或“长版/短版”的从属关系。

## 两条正式路线

| 版本 | 权威导演稿 | 叙事主角 | 目标时长 |
|---|---|---|---:|
| 人物版 | [`phase2-character-director-treatment.md`](phase2-character-director-treatment.md) | 一名真实历史官员贯穿绩效季，以个人遭遇带观众进入制度 | 约 `09:30`，允许 `08:00–12:00` |
| 制度群像版 | [`phase2-institution-director-treatment.md`](phase2-institution-director-treatment.md) | 制度及多人组织网络，追踪一个 C 如何被生产、批准和跨周期记账 | 约 `09:40`，允许 `08:00–12:00` |

两版的配置、authoring ledger、cut/run/artifact/output ID 与制作命令统一维护在
[`phase2-dual-cut-production.md`](phase2-dual-cut-production.md)。

## 双片交付登记（2026-09-03 继续执行）

本轮分别生成的人物版与制度群像版制作包见
[dual-video-production-packet-2026-09-03.md](dual-video-production-packet-2026-09-03.md)。

两条路线都是正式交付物，不互相替代：

- 人物版：[`phase2-character-director-treatment.md`](phase2-character-director-treatment.md) → `zhongguo-361-phase2-character-led.mp4`
- 制度群像版：[`phase2-institution-director-treatment.md`](phase2-institution-director-treatment.md) → `zhongguo-361-phase2-institution-led.mp4`

两套配置、authoring claims、审片计划和独立输出路径均已落盘。宣传工具已在可写 fresh clone
固定到 `origin/main` 的 `57c42fca13ea459432c1caf76e069a1fbccf602c`，并通过二期 builder 的 26 项测试；
正式 TTS/渲染仍必须等待 8/8 段真实 CK3 clean spans。当前两份 MP4 尚未生成，启动阻塞和可核验日志见
[`live-startup-blocker-2026-09-03.md`](live-startup-blocker-2026-09-03.md)。

最新一次双版本前置复核见
[`promo-preflight-audit-2026-09-03.md`](promo-preflight-audit-2026-09-03.md)，两份 runbook 位于
`_runtime/phase2-preflight-audit-20260903-0930/`，均诚实停在 `RED / footage_pending`。

`docs/` 保存两版的导演稿、生产合同、审片模板和状态索引；大体积 MP4 按项目约定落在外部
`artifacts/demos/YYYY-MM-DD/`（并在本页登记路径、时长、编码和 SHA-256），不把成片二进制塞进 Git。

## 交付进度（2026-09-03）

| 工作包 | 当前进度 | 下一项 | 预计时间点 |
|---|---|---|---|
| 二期产品代码与发布树 | B1 正式 generator split 已 full-entry GREEN；B2 为 25 片；Workforce effect 为 76 片且 B2 40-effect 闭包可精确选 16 片 | 拆分 Workforce 的 149-event 单体，再构造无 stub 的 B2 full-entry 候选；同树 GREEN 后才进 seed | 后续门通过后再估；不沿用旧 2–5 分钟线性启动估算 |
| 人物版最终片 | 导演稿、独立配置、authoring ledger、审片模板已完成；真实 footage `0/8`，尚无 MP4 | 取得 8 段 clean spans → 具名 source review → fresh-update promo tool → TTS/build/review/export | 素材齐备后再估；候选制作约 45–90 分钟，另加两轮真人审阅 |
| 制度群像版最终片 | 导演稿、独立配置、独立回切编排、authoring ledger、审片模板已完成；真实 footage `0/8`，尚无 MP4 | 同上，但独立生成旁白、候选、审阅和导出 | 素材齐备后再估；候选制作约 45–90 分钟，另加两轮真人审阅 |
| 宣传工具 | 可写 fresh clone 已完成 `git fetch origin main --prune`；HEAD 与 `origin/main` 均为 `57c42fca13ea459432c1caf76e069a1fbccf602c`，工作树干净 | 两版开始 TTS/渲染前复核同一 HEAD，并把该 checkout 注入 builder | 已满足更新门；正式渲染仍等待 8/8 clean spans |
| G2 / open_kaishek | G2 已按用户要求暂停；本轮 open_kaishek 仅对单个 B1 effect 做离线 parser smoke，真实正文 validator 仍有 `UNKNOWN_OPCODE`，IR/runtime `SKIPPED` | 仅在用户解除 G2 暂停后恢复 paused exact-build evaluator 双读；不得用 parser smoke 提升认证 | 暂无；当前不进入 native/runtime live |

这里的“尚无 MP4”是刻意保留的事实状态，不是漏写路径：没有真实八段 CK3 素材、具名审阅和 fresh tool receipt 时，制作器会 fail-closed，不生成占位宣传片。

## 最新实机边界（2026-09-03）

有效 profile 的最新对照已改变启动判断：显式非空 disposable `-userdir`、完整 `pdx_settings.txt/account/dlc` 与 warm DX11 cache 下，无 Mod 裸跑 42.253 秒到达 `Frontend`；当前 Release bridge 54.634 秒、RBX guard candidate 45.582 秒也都到达 `Frontend`，并以 `WM_CLOSE`、exit `0`、cleanup proven 收尾。早先缺 profile 资产的 direct probe 仍可在 `ck3+0x1DABD89` 崩溃，但不能再据此宣称 CK3 本体完全打不开。剩余 RED 是 Phase2 broad/workforce 依赖闭包与事件本地化 fan-out；event-locaug 虽出现窗口和 `frontend_main.gui`，但未完成 history load。对应 crash dump、session cleanup 和 relay 日志保存在
`Z:\\ck3_mod_rewrite\\_runtime\\phase2-seed-20260903\\`，这些运行均没有产生满足合同的可入片游戏素材，当前 footage 仍是 `0/8`；详细分层见
[`manual-vs-automated-launch-diagnosis-2026-09-03.md`](manual-vs-automated-launch-diagnosis-2026-09-03.md)。

宣传工具已在可写 fresh clone `Z:\\ck3_mod_rewrite\\_runtime\\promo-tool-fresh-20260903` 更新并核对到 `origin/main`（`57c42fca13ea459432c1caf76e069a1fbccf602c`）。等 CK3 启动/seed 边界修复并取得八段素材后，仍会分别完成两版 TTS、字幕、候选、人工审阅、导出和独立哈希记录。

实机启动复现、解锁条件和诚实 ETA 见 [`live-startup-blocker-2026-09-03.md`](live-startup-blocker-2026-09-03.md)。

最新 A/B 结果：冷/不完整 profile 的 `-noWorkshop` 以及 `--userdir=<isolated path>` 探针仍在同一 `ck3+0x1DABD89` 崩溃；复用完整有效 profile 后裸跑、当前 bridge、RBX guard 均 GREEN。Steam `-applaunch` 入口仅是 no-launch harness 结果。详细回执见 [`live-startup-probe-no-workshop-2026-09-03.md`](live-startup-probe-no-workshop-2026-09-03.md) 与 [`ck3-startup-recovery-live-evidence-2026-09-03.md`](ck3-startup-recovery-live-evidence-2026-09-03.md)。

两版的独立审片入口为：

- 人物版：[`review/character-led-review-plan.md`](review/character-led-review-plan.md)
- 制度群像版：[`review/institution-led-review-plan.md`](review/institution-led-review-plan.md)

每个入口都包含第一轮原始素材/声明审阅和第二轮最终候选片审阅模板；模板不是通过回执，只有绑定真实媒体字节并完成全长 `1×` 审阅后才能签核。

## 共同素材与独立交付

两版共享同一套真实二期证据基础：十个 canonical authoring chapters，其中开场/结尾为双语生成卡，中间为八个真实 CK3 clean spans。共享 source span 是为了避免重复制造游戏事实，不代表两版是同一条视频。

两版必须分别拥有并验收：

- 独立的项目配置、剪辑时间线、中文旁白和中英双语字幕；
- 独立候选视频、媒体探测结果和 SHA-256；
- 独立 claims audit 与两轮 1× 完整人工审阅/sign-off；
- 独立导出记录；若外部发布，还要分别保存明确发布回执。

任何一版通过或发布，都不能替另一版自动签核。人物版不得用蒙太奇伪造同一人物因果；制度版不得把不同角色、案件或周期伪装成一条连续游戏内因果。共同的实机事实、authoring/claim 边界、有效 footage intake、媒体门禁和真实证据要求继续生效。

## 路径与同步规则

本目录中的两份 treatment 是导演内容的 **canonical authority**。`mod_zhongguo_style/promo/` 下保留同名入口文件，仅用于兼容原有浏览路径并指向这里；不得在两个目录分别维护两份正文。后续导演修改只编辑本目录的权威稿。

项目配置、authoring claim matrix、capture contract、媒体构建和 readiness 状态仍由各自原有文件负责。导演稿只定义叙事与拍摄方案，不会自行把 `planned`、`static-ready` 或候选素材提升为 live、complete、exported 或 published。

## 最新 seed preflight 回执（2026-09-03 06:51）

以 clean freeze `165b47742fd05ff3713b8be4452711002328d57d`、source ZIP SHA-256
`77aa3e30f1c20763576dbeea71b1c7451cfd63a15fb53a46fc58a373d72338e8`、guard-on bridge 和同步
open_kaishek `981c79388a07e447b18f8e4472a16fd65e28c083` 重新执行 `--preflight-only`：结果 `GREEN / preflight-ready`，source/archive、依赖、projection、bridge 和静态测试均 GREEN，`ck3_launch_attempted=false`；seed 合同仍为 `blocked_seed_generation_required`，因为尚未取得新真实 seed。回执位于
`_runtime/phase2-seed-20260903/artifacts-preflight-current-03/preflight.json`，SHA-256
`9057F967CFE97036AD4E3918C2640892371EBB006BBADDE18EE36DA7A4CABE2E`。这确认后续实机采集入口可直接复用，但不等同于 live 或视频完成。

### 30 分钟完整投影轮次（已结束；monolith control）

`formal-phase2-full-exact-1800-20260903` 已完成并封存。该轮实际挂载的是未拆分 monolith（264 files / 15,937,535 bytes），不是目标 exact A+B 树；report SHA-256 为 `241254233107098CF5F385F1C4472D94CA3E1C8D93D6CFFF869A8C38C0F7A79A`。结果为 `timeout`，最后停在 `Total of : 881`，未到 `Frontend`/history，`error.log=0`，CK3 exit `1`，cleanup 已证明。因此本轮只能作为非拆分 control，不能用来判定 split 功能 GREEN。

随后 B7 workforce stub 的 300 秒轮次仍在 `Total of : 881` 停止，Frontend/history 均为 false，结论保持 RED。7200 秒续测已取消，不再创建 `formal-phase2-full-exact-7200-20260903`。当前改按 [`phase2-incremental-startup-batch-plan-2026-09-03.md`](phase2-incremental-startup-batch-plan-2026-09-03.md) 推进；第 1 批 `core-current` 已实际启动，并于 15:04:20 同时到达 `Frontend` 与 `End loading of history`。该批启动层为 `STARTUP_GREEN`，但整体报告仍为 RED：observer coverage 只报 `heartbeat_not_observed`，`error.log` 同时记录 projection-missing symbols（含 `Unknown effect`/trigger 等）。因此当前分类是 `STARTUP_GREEN / PARSER-或-PROJECTION_RED`，不是完整功能 GREEN。旧 `4ff` preflight 的 `ck3_launch_attempted=false` 仍只算启动前配套 RED，不计作 CK3 启动失败。

### B1 effect 拆分最新实机边界

未改写的 58-file、单 effect full B1 仍只有一次 `1205.343 s` pre-menu RED。随后 all-stub（255.113 s）、left-real（180.403 s）、right-real（178.968 s）、event-root closure（181.360 s）、excluded-A（193.588 s）、excluded-B（184.817 s）以及 all-but-76（保留 77 个真 block 中的 76 个，171.228 s）均取得 full-entry GREEN。

进一步的 `balanced-files` 候选没有 stub，保留全部 77 个定义且逐 block 正文字节与原始 effect 一致，只把单文件拆成两份；它为 59 files / 7,858,264 B，两份 effect 分别为 255,134 B 与 240,709 B，并在 180.396 s 取得 full-entry GREEN。因此拆文件已是可实施候选，但现有样本不能唯一证明根因，也不能把原始未改写 full B1 改写为 GREEN。产品全量、seed 与素材门仍未通过，真实 footage 保持 `0/8`，两条 MP4 仍不存在。

本轮 open_kaishek 只覆盖单个 effect 文件的离线 parser smoke；含真实正文的候选 validator 仍报 `UNKNOWN_OPCODE`，IR/runtime 均跳过。该结果不构成 B1 语义、CK3 native/runtime 或 G2 readiness 证据；G2 继续保持用户要求的暂停状态。

### 正式 B1 generator split 与 r3 验收

正式生成器已将 B1 effect 物化为两个文件，分别包含 `41 + 36` 个定义；候选为 **59 files / 7,858,254 B**，全部定义按顺序重组后的正文与原始单文件 **exact**。formal tree SHA-256 为 `9EED00504E1AAF34F352B440CFB4DFEBF3BB1206966457834727A81BAB4FC50A`。

r1/r2 均在约 0.3 秒因 probe game-path 配置错误结束，`ck3_started=false`，只保留为 harness/config RED，不计作内容失败。修正后的 r3 用时 **245.770 s**，8/8 entry gates、3 个 game-state markers、material error 0 与 cleanup 全部 GREEN。B1 checkpoint 因而晋级为 **startup/full-entry production-candidate GREEN**。

该晋级不覆盖 delayed-path、seed、生产 OODA 或 footage；真实素材仍为 `0/8`，两条 MP4 仍未生成。原始未拆分单文件 full B1 的唯一 1205.343 秒 RED 继续保留；拆分是已验证的实施候选，但根因仍未唯一证明。G2 保持 paused。

### B2 generator 用途分片（2026-09-04）

B2 的 `253,920 B / 152-effect` 旧单体已由 generator 替换为 25 个用途分片；152/152 个顶层正文逐 block 字节一致，每片
`1–9` 个、合计 `250,551 B`，清单 SHA-256 为
`06274A5E0D89EF97C19EF3C099E8AEF946C4153BC78C065EC260806D27F67FAB`。broad/release 均包含全部分片且不含旧单体；
当前仅为文件布局 `static-ready`，没有新增 CK3 live。完整映射与限制见
[`361-b2-runtime-spec.md`](../../mod_zhongguo_style/docs/361-b2-runtime-spec.md)。

Workforce 的 `4,636,271 B / 324-effect` 旧单体也已由 generator 替换为 76 个用途分片，324/324 顶层 block 逐字节一致，
每片 `1–10` 个且没有超限例外。B2 所需的 40 个 Workforce effect 恰好映射到 16 个完整分片（341,602 B，
extra=0、missing=0）；全量分片清单 SHA-256 为
`E5DD22CEF71D60E069884A27BE924234B4FAD42490AEF2B52B966AFD95585858`。当前仍只有静态证据。

无 stub 的 B2 production closure 还需要把 `168,729 B / 149-event` Workforce event 单体按用途拆开；否则完整 event 文件会引用约
210 个 Workforce effect，重新拉回几乎全图。权威固定点是 `71 effects / 28 events`，旧 `68/24` 漏扫了 `EVENT = <id>` 参数 ABI。
不能把旧的 P2/P3 startup/projection RED 或 stub 候选冒充正式 B2。
