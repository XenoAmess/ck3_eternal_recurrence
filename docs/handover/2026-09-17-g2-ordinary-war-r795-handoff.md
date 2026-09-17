# G2 ordinary campaign / R795 handoff（更新至 R806）

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

- 远端 `master` / 包内 agent source：`9bacc5af2980cbd70767e8350f1262db60019e23`。
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

## 下一单实例队列

1. Council 优先：基于 R794 history260 的 occupied steward 31507 场景，执行一次隔离、只读、action-OFF 的 final-gate query。只有 provider row 的真实 isolated guest、candidate-pending 或 `incumbent_fireability_evaluated=true && incumbent_can_be_fired=false` positive 才能关对应门；全空则停止重复该 checkpoint。公共 Council query/action/广告保持 OFF。
2. War：从 R806 最终 pair 继续当前 WarID25，先读取同帧 termination/战斗上下文，再按合同比较 continue/white peace/surrender 并最多提交一个合法动作。GEN-034 C/D 仍要求自己的 Raiktor-specific projection/evaluator、物质战后结果、truce/war disappearance、checkpoint 和 cold restore。
3. 自然事件/继承：并入后续普通 production 长跑。临死前重新冻结 title 分配，要求同 campaign 自然角色切换、真实继承人动作、paired checkpoint 与新进程恢复；不得沿用旧 heir 值或 fixture 结论。
4. 治理、家庭外交与 M6/M7 只补会阻塞标准封建连续运行的最小 typed 闭环，不开展展示、广矩阵或策略精雕。

## 当前现场与约束

- R806 结束后 CK3 与 injector 四路盘点均为 0；下一次启动必须重新盘点并分配 R807 或更高实际空闲轮次。
- R806 mutable state：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-9bacc5af-r804-state`；最终 pair 已冻结到 `D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-9bacc5af-r802-qualification\final-pair-r806`。
- 当前 clean integration clone：`C:\workspace\g2-war-r794-no-safe-exit-20260917`；共享 `Z:` 工作区有历史改动，不 reset/clean。
- 运行 artifact/checkpoint 继续写 `D:\ck3_mod_rewrite_process_assets`，轮次 ledger 在 `C:\ck3_mod_rewrite_process_assets\ck3-single-instance-rounds`。
- 禁止 merge commit、强推 master、并发 CK3、改运行中加载文件、盲重提未确认动作、提前广告未验收能力，或把本包称为整局/G2 complete。

## 读取顺序

1. 本文与 [预览包交付页](../ck3-native-ai/g2-preview-release.md)；
2. [G2 权威合同](../autonomous-agent-progress/g2-requirements-v1.json)；
3. [`../autonomous-agent-progress/daily/2026-09-17.md`](../autonomous-agent-progress/daily/2026-09-17.md) 与 [`../autonomous-agent-progress/weekly/2026-W38.md`](../autonomous-agent-progress/weekly/2026-W38.md)；
4. R804/R805/R806 closed ledgers、formal reports 和 operator receipts；
5. [`../ck3-native-ai/player-war-exit-policy.md`](../ck3-native-ai/player-war-exit-policy.md)、[`../ck3-native-ai/g2-preview-operator.md`](../ck3-native-ai/g2-preview-operator.md) 与 MCP 迁移文档。
