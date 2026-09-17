# G2 ordinary campaign / R795 handoff（更新至 R835）

交接时间：2026-09-17（Asia/Shanghai）

权威 G2 合同：[`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## 用户当前可取得的交付

当前用户可运行包已从旧 R783 更新为 R802 冻结包，并完成 R804–R806 实机资格链：

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r802-9bacc5af-stage-20260917\g2-preview-ordinary-9bacc5af-r802.zip`
- ZIP SHA-256：`E32D2057B28641CE78C76F11C478704AA2EEBA549D8C30F7228C88F28DAA1273`
- GO manifest SHA-256：`CAA552E05117A80C696C1BBBF46EA257E936F0C977E706310926E49DA9EBD4E5`
- live qualification SHA-256：`9F7DA87BDEDA3C3C41D50831C5D6EAB724F8DE669586090ED10B8D60B10C1AA3`
- 启动、停止、checkpoint、cold restore 与支持边界：[`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)

这是可启动的 bounded ordinary preview，不是整局交付。G2 权威状态仍为 **1/8**（仅 M1），Council final gate **1/4**，GEN-034 **2/4**；首条 1066→1453 和第二种子都未验收。

## Git 与冻结组合

- 当前远端 `master`：`f00e57f1acfc1f71f7bac6e0e4a144d492013337`。
- 已交付包内 agent source：`9bacc5af2980cbd70767e8350f1262db60019e23`。
- Native source：`881e1ba5467f3304d930faaa958cdafd24962370`。
- CK3：`1.19.0.6`，EXE SHA `2D00FF31...DB86`。
- DLL：`DA7CA992...D3B7`；injector：`46D43267...75F`。
- production tree：`8471F6B4...0367`，86 files。
- lifecycle：`feudal_government / xar_off / ordinary_campaign_succession / no pact`。

包构建器新增 deterministic stage/finalize/assemble/verify/promote 流程。资格前修复了三个实际封包 B0：环境文件字节哈希误当逻辑 digest、ZIP 丢失空 Git 元数据目录、`prepare-state` 生成未忽略 runtime cache 导致新解压树变脏。聚焦测试 normal 与 `-O` 均为 5/5；两次 assembly 得到相同 ZIP 哈希。所有临时 Git 分支已在线性快进后删除，无 merge commit 或 force push。

## R804–R806 资格链

| 轮次 | 结果 | 证据 |
| --- | --- | --- |
| R804 | fresh-extraction eligibility GREEN | 9/9；actor31853/date53150976/feudal/xar_off/空活动上下文；PID205880 回收；report `31B13D0F...76D30` |
| R805 | formal production + controlled stop GREEN | 13/13、6 gameplay；query declarable → typed declare → 独立 WarID25 → 下一 turn 消费 → raise/move/battle；history316 checkpoint `96058952...FAE6`、driver `348FF39E...C047`；旧白和平重放0；PID167232 回收；report `EE0CBC02...719AF` |
| R806 | new-process cold restore GREEN | PID52284 精确恢复 R805 pair、同 actor/episode/WarID25/Army304；5/5、2 gameplay、date53151912→53152848；重复宣战0、旧白和平重放0；最终 checkpoint `E2044A6B...CD7B`、driver `A34BEBBF...B4FF`；完全回收；report `3F09893F...ED1F2` |

外部资格输入 SHA `655B2AE3...C6129`，GO 收据 SHA `9F7DA87B...C1AA3`。晋升前后 ZIP SHA 完全相同。

## 已关闭的 ordinary WarID 5 链

R800 只读确认历史提交在 durable checkpoint 上为 `exact_absent`；R801 同帧比较 continue/white peace/surrender，仅提交一次 `offer-white-peace-5`，独立观察 WarID 5 消失并在下一 turn 清理 Army 33；R802 新进程 cold restore 和 postwar cooldown 后没有重提或立即再宣战。该 exact branch 是 production-live loop，但不替代 Raiktor-specific GEN-034-C/D，因此 GEN-034 保持 2/4。

## R807–R835 Raiktor 推进与赎金恢复

- R807 是旧运行时 `300s` readiness 上限的零动作 RED。R808–R831 从 R732 的 Raiktor WarID33554473/history178 继续同一 episode，完成多段正式行军、撤退与两次战斗；R831 到达 player-relative score `-100`，但三路评估器仍把 continue 视为 eligible。
- R832 在继续路线 sentinel 期间由 CK3 自然结束战争，没有提交 white peace 或 surrender。它清理两支残余军队，运行两个和平 turn，并保存 history669/date53203752，checkpoint `E45F1CE7...BB001`、driver `C327EF26...872CE`。这是有效的自然战后与后续消费证据，但不满足 GEN-034 C/D 的“推荐 → 唯一 semantic terminal action → 物质后置 → 恢复”合同；权威计数保持 `2/4`。
- R833 从 R832 pair 做真实新进程冷恢复，确认旧 WarID 缺席、旧战争动作未重放并完成两个和平循环，随后在 pending interaction 到达边界时 fail-closed。R834 用旧封存 runtime `1f117ab8` 重现 exact `ransom_interaction`，因为该版本尚未包含分类而在 turn8 零回复停止；report `943C374F...258A`，失败状态完整保留。
- 先行尝试把 R832 绑定到普通 `xar_off` 预览环境时，操作器发现源 profile 实际为 `xar_on` 且旧 driver 没有 ordinary lifecycle anchors，遂在无 CK3、无轮次阶段拒绝重绑定。不得把该 Raiktor save 冒充 ordinary preview 证据。
- R835 改用已交付 `9bacc5af` agent / `881e1ba5` native 和独立 `xar_on` profile，冷恢复同一 R832 pair。20/20 turns、16 queries、4 gameplay 全绿；两次自然 `ransom_interaction` 分别在 history678→679 与 687→688 完成 exact query、一次 typed reject、独立 paused frame 旧 ID 消失，随后正式策略继续且 history694 成对 checkpoint。report `4ABB17D8...C1C2`、driver `99047F37...FDC0`、checkpoint `B75E7606...DF30`；WarID33554473 全程缺席，进程完全回收。
- R835 只关闭旧 runtime 暴露的赎金连续运行 B0，且仅按其真实 `xar_on / rogue_one_life` 范围记账；它不扩张 ordinary preview 广告，也不关闭 GEN-034 或新的 G2 里程碑。

## 下一单实例队列

1. War：修复已实证的 Raiktor `-100` 资格缺口。只在同帧、primary-attacker、player-relative `<= -100` 的完整原生终局控制输入成立时，把 continue 留在 trace 但标为 ineligible；随后仍由合法 white peace/surrender 比较，输入不完整则 fail-closed。聚焦 normal/`-O` 通过后，从 R831 pre-terminal pair 启动一个新轮次，要求唯一 typed terminal、物质战后状态、下一 turn、paired checkpoint 与 cold restore。
2. Council：R797 已证明 occupied-steward 场景只增加 already-councillor 证据，不重复该 checkpoint。等待真实 guest、candidate-pending 或 replacement-fireability denial 的 materially different scene；公共 query/action/广告保持 OFF。
3. 普通 campaign：继续已交付 R806 ordinary pair，优先自然 `.0030` / `.1007`、同 campaign 自然继承和会卡住时间推进的治理状态；不得用本节 `xar_on` Raiktor pair 替换 ordinary 证据。
4. 治理、家庭外交与 M6/M7 只补会阻塞标准封建连续运行的最小 typed 闭环，不开展展示、广矩阵或策略精雕。

## 当前现场与约束

- R835 结束后 CK3 与 injector 盘点均为 0；下一次启动必须重新盘点并分配 R836 或更高实际空闲轮次。
- Ordinary R806 mutable state：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-9bacc5af-r804-state`；最终 pair 在 `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-9bacc5af-r802-qualification\final-pair-r806`。
- Raiktor R835 资产：`C:\ck3_mod_rewrite_process_assets\g2-ransom-r835-current-runtime-xar-on-20260917`；R831/R832 原 pair 仍在 `C:\ck3_mod_rewrite_process_assets\g2-gen034-c-r807-raiktor-20260917`。两条 lifecycle 不得混用。
- 当前 clean integration clone：`C:\workspace\g2-war-r794-no-safe-exit-20260917`；共享 `Z:` 工作区有历史改动，不 reset/clean。
- 运行 artifact/checkpoint 继续写 `D:\ck3_mod_rewrite_process_assets`，轮次 ledger 在 `C:\ck3_mod_rewrite_process_assets\ck3-single-instance-rounds`。
- 禁止 merge commit、强推 master、并发 CK3、改运行中加载文件、盲重提未确认动作、提前广告未验收能力，或把本包称为整局/G2 complete。

## 读取顺序

1. 本文与 [预览包交付页](../ck3-native-ai/g2-preview-release.md)；
2. [G2 权威合同](../autonomous-agent-progress/g2-requirements-v1.json)；
3. [`../autonomous-agent-progress/daily/2026-09-17.md`](../autonomous-agent-progress/daily/2026-09-17.md) 与 [`../autonomous-agent-progress/weekly/2026-W38.md`](../autonomous-agent-progress/weekly/2026-W38.md)；
4. R832/R834/R835 与 R804/R805/R806 closed ledgers、formal reports、evidence seals 和 operator receipts；
5. [`../ck3-native-ai/player-war-exit-policy.md`](../ck3-native-ai/player-war-exit-policy.md)、[`../ck3-native-ai/g2-preview-operator.md`](../ck3-native-ai/g2-preview-operator.md) 与 MCP 迁移文档。
