# G2 ordinary campaign / R795 handoff

交接时间：2026-09-17（Asia/Shanghai）

交接范围：可运行预览、普通封建连续运行、R794 战争 RED 修复、R795 冷恢复候选、Council 后续场景、MCP 升级迁移与 Git/CK3 现场。

权威 G2 合同：[`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## 当前结论

用户现在可以取得并启动已经验收的 bounded ordinary preview；它仍是当前唯一可交付预览，不代表整局完成：

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r783-stage-20260916T134805Z-6cfba744\g2-preview-ordinary-5ac64152-r783.zip`
- ZIP SHA-256：`AA9CABB5D4CA709E55AB367A94D0C58A088AAD20D540B76F7990DAD1FC81517C`
- GO manifest SHA-256：`A5CB85FE0D9BF96EF844B68055532220498FE8E298F8B2769515EC026AAD4B1D`
- live qualification SHA-256：`1EF45C2B14D43C6AA2E953D5BB0E56925F181CDC3819FA3ECE70BCC6F7E5361A`
- 启动、状态、停止、checkpoint、恢复和支持边界：[`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)

正式 G2 仍为 **1/8**，只有 G2-M1 complete。合同的 `percent_reporting_allowed=false`，因此正式状态继续写 1/8；如只做算术说明则是 12.5%，不得把它当成项目完成度。Council final gate 为 **1/4**，GEN-034 为 **2/4**。首条 1066→1453 整局仍是 **0/1 已交付**，年代推进比例未知且不足以从当前局部窗口外推。

## Git 基线与本轮已交付代码

本文编写前，远端 `master` 已线性快进到 `966c45a25b0388b0d85d8824be5c08aa14932dc6`。本文提交后，以包含本文的最终远端 `master` 为 Git 交接点；R795 所需运行时代码从以下两个连续提交开始已经完整：

| 工作包 | master commit | 结果 |
|---|---|---|
| WP-WAR-R794 exact de-jure white peace | `d6c683eaba0ce1e958f275447f752da4cab842cc` | strategy、native driver 与 `native_auto_run` 同时接通 exact `individual_county_de_jure_cb` 正战分无安全路线白和平 |
| WP-WAR-R794 one-shot fence | `966c45a25b0388b0d85d8824be5c08aa14932dc6` | 同 episode + WarID 的 `submitted_pending/applied` 永久阻断重复提交；不改变既有 `claim_cb` 30 日语义 |

补丁范围严格限定为：CK3 exact build 1.19.0.6、CB database index 17 / `individual_county_de_jure_cb`、玩家为 primary attacker/leader、单 targeted title、`0 < score < 100`、战争至少 180 日、所有 exact 路线已证明不可安全执行、fresh same-frame white-peace validator/available、AI acceptance raw 正数且最终 recipient `would_accept_now=true`。策略显式记录 continue / white peace / surrender 三项，只选择一次 white peace；旧 termination row 只能促成 fresh query，不能直接动作。

聚焦验证：

- 实现者 normal / `-O`：R794、white-peace、negative-termination、R767、exact-siege，以及 driver/auto-run 对应聚焦组均 GREEN。
- 协调者复验：R794 normal 4/4；white-peace normal 12/12；R767 normal 2/2；driver white-peace 3/3、R767 1/1；auto-run white-peace 5/5、R767 1/1；R794/R767 optimized 聚焦组 GREEN。
- one-shot fence 复验：native driver `-k white_peace` normal 4/4、`-O` 4/4。
- 无 native ABI、MCP schema、公开 capability 或广告变化；不需要新的 `open_kaishek` 适配。能力仍按原门禁发布。

## R794 真实运行与 RED

R794 从 R793 history 245 冷恢复，实机证明前一轮 siege 修复生效：

1. 重放 battle terminal；
2. turn 5 typed `start-assault-6`；
3. turn 6 独立推进 1 游戏日并观察 assault progress；
4. turn 7 typed `stop-assault-6`；
5. turn 8 观察 7 日 siege progress；
6. 保存 history 260 / date `53149872` checkpoint。

随后 history 261 查询 campaign root、262 查询 termination、263 发生未落盘 6 日推进、264 再查 root；turn 11 以 `native_war_no_safe_exact_route` RED 停止。该失败帧 `selected_step=null`、`result=null`、未提交动作，动作不确定性为零。R794 完整回收 CK3 与 injector。

- formal report：`D:\ck3_mod_rewrite_process_assets\g2-r794-war-siege-recovery-c114759\formal-replay-02\formal-report.txt`
- formal report SHA-256：`F155E2DD2D0AB6B0932B5C46EEE0903FBA140C9E24CA6EFB8B667F1F5A6C1A6D`
- operator receipt SHA-256：`ED609F6B81B744243A11EAE6247F880D03FD279AAEC8DC74C0A0B206C0D61CE4`
- independent recovery seal：`D:\ck3_mod_rewrite_process_assets\g2-r794-war-siege-recovery-c114759\evidence\R794-post-run-seal.json`
- seal SHA-256：`C67F30556E075C14819ED8405C00A92B7677CA9B9EDB20E4A31DCA6D4A0B5842`
- closed ledger：`C:\ck3_mod_rewrite_process_assets\ck3-single-instance-rounds\R794-closed.json`
- closed ledger SHA-256：`768C9CA80FA10CA015CC799829161668FDBF9076F8C9FCA6FC77AD754D2857FB`

独立 seal 的结论是唯一恢复点为 history 260。history 261–264 必须放弃；其中 263 的 6 游戏日推进未落盘，不能累计认定。

## 下一位同事的唯一首要动作：R795

R795 已完成只读 staging，但**尚未分配轮次、尚未执行 prepare/rebind/preflight、尚未启动 CK3**：

- stage：`D:\ck3_mod_rewrite_process_assets\g2-r795-cold-stage-r794-h260-20260916T162722Z-845327f5`
- `source-inventory.json` SHA-256：`279D90F3DE425CCBD55A5D3E5B3D1B29E80152710EEB10426BD0D9BF83623109`
- `SHA256SUMS.txt` SHA-256：`64D1D35B7A3F99CA9D3B1CD04D8DD471440578E2408CBF35B8875DCF12BE0073`
- checkpoint SHA-256：`55A51F5D6329C2682C9108FB190BDE10592BA19EBC4AF518671290E17B1FDE82`（54,676,707 bytes）
- source driver SHA-256：`0B83F6CE0CB69E88ED6E92E6369C55F87AFC0C92506055A21F7E418EA57959AA`（2,198,095 bytes）
- 参数化 prepare 命令：`after-new-commit-commands.json`

严格按以下顺序继续：

1. 读取本文、AGENTS.md、权威 G2 合同和 `source-inventory.json`；核对远端 `master`、当前 clean source commit 和 stage 哈希。
2. 即时确认所有受管环境 `ck3.exe=0`、injector=0；R794 已关闭，但不能用旧检查代替本次检查。
3. 在 `after-new-commit-commands.json` 中把 `SourceRepo` 与 `ExpectedCommit` 绑定到同一个实际 clean source。执行其中的 no-launch `prepare-state`；它负责 copy/rebind/preflight。任何失败均不得分配轮次或启动游戏。
4. 核对 prepare 生成的 environment、rebind receipt、checkpoint 和 target driver SHA；save bytes 必须仍为 `55A51F5D...FDE82`，cold restore 必须截断 history 261–264。
5. 只有 no-launch 结果 GREEN 后，创建持久 `R795-allocated.json`，记录 exact build/EXE、agent/native/DLL/injector、DLC/mod/load order、source/target pair、参数、超时和启动前进程 inventory。
6. 通过正式 `tools/g2_preview_operator.py run` / `native-auto-run` 启动一个新 CK3 进程。预期链为：cold restore history 260 → fresh campaign root / termination query → exact route exhaustion → 同帧 continue/white peace/surrender 比较 → 最多一次 `offer-white-peace-5`。
7. ACK 只记 submitted。若 `submitted_pending`，先只读确认 WarID 5 的实际状态，禁止在 30 日后或任何时间盲重提。代码 fence 会持续阻断同 episode + WarID 的重复提交。
8. GREEN 需要独立后帧证明旧 WarID 5 消失，核对可观测 truce/战后物质状态、下一 turn 消费、postwar checkpoint 与完全进程回收。任一未知或 RED 仍按 RED SOP 封存，不重试未确认动作。
9. R795 成功后另分配 R796，真正新进程 cold restore postwar checkpoint，先确认旧动作已生效且未重提，再继续同一高层目标。只有这一链完成后才恢复普通 campaign 长跑。

R795/R796 即使成功，也只关闭 ordinary campaign 当前 B0，并提供普通战争终局证据。权威 GEN-034-C/D 仍绑定 Raiktor-specific same-frame projection/evaluator、recommendation、动作与 postwar/cold-restore 合同；不得把 GEN-034 从 2/4 擅自改为 4/4。

## R795/R796 后的 Council 队列

R794 history 261 与 264 的 public campaign root 显示六个核心职位已占用，steward 为 CharacterID 31507 / `task_collect_taxes`。这相对旧的 vacant 场景值得做一次 replacement private query，但它只证明 occupied：public `frozen=false` 不是 fireability，顶层 `pending_character_interaction=null` 也不能关闭 candidate-pending。

战争终局与 R796 cold restore 完成后，在新的 paired paused checkpoint：

1. fresh public root 仍显示 steward occupied 时，封存一个 query-only Council candidate；
2. 只运行一次现有 private final-gate query；
3. 只有 provider row 实际产生 `incumbent_fireability_evaluated=true`、`incumbent_can_be_fired=false` 和非空 replacement isolated list，才关闭 replacement gate；guest/pending 同理要求各自真实 isolated positive；
4. 任一 positive 出现后，才从同一 exact paused scene 封 action-ON candidate做 typed rejection；三个列表全空则停止重复该 checkpoint，继续 campaign 等 materially-different scene。

Council 当前仍为 1/4：already-councillor 已闭合；guest、candidate-pending、replacement fireability 保持 OPEN；公开 Council query/action/广告保持 OFF。

## MCP 地址方式与 CK3 升级迁移

权威评估已落盘：[`../ck3-native-ai/mcp-ck3-addressing-and-upgrade-migration.md`](../ck3-native-ai/mcp-ck3-addressing-and-upgrade-migration.md)，对应已在 master 的提交 `bc382cfae8998084ecf62088dd6bc7a27e1740d8`。

当前实现不是“对任意新版本自动特征码定位”。运行时先固定 exact EXE SHA，再用 module base + 该 build 的 RVA/layout/ABI；特征码主要用于离线派生和已知位置复核。CK3 升级时应创建独立 frozen adapter，重新确认 EXE SHA、调用链、RVA/layout/vtable/枚举/线程与生命周期语义，先过 static/fixture，再做 paused live read、typed action/result、checkpoint/cold restore，最后才重新注册或广告受影响能力。未知 build 必须 fail closed；不得沿用旧 RVA，也不得把 signature hit 当成完整 ABI 兼容。

## 进度与未来基线

| 交付面 | 当前状态 |
|---|---|
| 可运行 bounded preview | GO，已交付 |
| G2 权威状态 | 1/8；仅 M1 complete |
| Council final gate | 1/4 |
| GEN-034 | 2/4；C/D blocked_live |
| 首条 1066→1453 整局 | 0/1 已交付；当前过程比例不可可靠外推 |
| 双种子“比较正常” | 0/2 已验收 |

计划基线继续为：2026-09-20 Council，09-25 GEN-034 C/D，09-30 自然事件/继承，10-08 和平治理，10-14 家庭/外交/战争联合评分，10-18 百年门，10-23 首条整局，11-06 第二种子，11-20 风险缓冲，2026-12 中旬至 2027-01 为 G2 8/8 展望。日期是工程目标；证据提前满足就提前交付，不为日期等待，也不把日期当验收结果。

## 现场、清理与不得误报的事项

- 本次交接不启动 R795；交接收尾时应再次确认 CK3/injector 为 0。
- 远端临时分支 `codex/g2-war-r794-no-safe-exit-20260917` 已在 `966c45a` 快进进入 master 后删除。
- patch clone `C:\workspace\g2-war-r794-no-safe-exit-20260917` 已确认 clean、tip 已集成、无独有提交，但物理递归删除被自动审批以 `blocked by policy` 拒绝；标记为“已集成，清理阻塞”，解除条件为删除策略允许。不得因此阻塞 R795。
- 三个已无 Git 引用或占用的报告 clone 仍因同一自动删除策略残留：`C:\workspace\r793_daily_close_20260917`、`..._b_20260917`、`..._c_20260917`。不得把它们当成活跃工作包。
- `Z:` 曾为 0 可用空间；继续把运行 artifact/checkpoint 写到 `D:\ck3_mod_rewrite_process_assets`，使用 `C:` clean clone 做 Git 集成。不要 reset/clean 共享 `Z:\ck3_mod_rewrite` 历史工作区。
- 禁止 merge commit、强推共享 master、同时启动多个 CK3、盲重提未确认动作、提前广告未验收能力，或把 ordinary R795 结果冒充 Raiktor GEN-034 C/D。

## 交接读取顺序

1. 本文；
2. [`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)；
3. [`../autonomous-agent-progress/daily/2026-09-17.md`](../autonomous-agent-progress/daily/2026-09-17.md) 与 [`../autonomous-agent-progress/weekly/2026-W38.md`](../autonomous-agent-progress/weekly/2026-W38.md)；
4. R794 independent seal；
5. R795 stage 的 `source-inventory.json`、`operator-manifest.template.json`、`after-new-commit-commands.json`；
6. [`../ck3-native-ai/player-war-exit-policy.md`](../ck3-native-ai/player-war-exit-policy.md)、[`../ck3-native-ai/g2-preview-operator.md`](../ck3-native-ai/g2-preview-operator.md) 与 MCP 迁移文档。

下一位不要先重跑 R794，也不要先做 Council。先完成 R795/R796 的一次终局动作、物质后置结果与真实 cold restore；随后立刻消费当前更有价值的 occupied Council scene。
