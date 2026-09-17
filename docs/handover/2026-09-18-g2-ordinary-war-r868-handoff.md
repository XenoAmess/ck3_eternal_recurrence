# G2 ordinary campaign / R868 handoff

交接时间：2026-09-18（Asia/Shanghai）

权威合同：[`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)

## 一句话状态

用户现在仍可取得并启动 R802 冻结预览包；本轮在源码侧关闭了普通封建战役的“首都接触 -> 实战 -> 战后重新集结 -> native rally 守势等待”B0，并把下一恢复点推进到 h1347，但尚未把累计源码重新打成并通过资格验收的新 ZIP。

## 用户当前可取得的交付

- ZIP：`D:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-r802-9bacc5af-stage-20260917\g2-preview-ordinary-9bacc5af-r802.zip`
- ZIP SHA-256：`E32D2057B28641CE78C76F11C478704AA2EEBA549D8C30F7228C88F28DAA1273`
- GO manifest SHA-256：`CAA552E05117A80C696C1BBBF46EA257E936F0C977E706310926E49DA9EBD4E5`
- live qualification SHA-256：`9F7DA87BDEDA3C3C41D50831C5D6EAB724F8DE669586090ED10B8D60B10C1AA3`
- 启动、状态、停止、checkpoint、cold restore 与支持边界：[`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md)

R802 仍是有效 GO 包，不应在新包拿到外部 GO receipt 前下架。它是 bounded ordinary preview，不是 1066→1453 整局交付。

## 最终 Git / 版本组合

- 已推送远端 master 的功能 tip：`a0fc877e1235a91f69a34915eb8679588f6ea89f`
- WAR-R867-B0 原提交：`649731adaac45dffa2437a21cccffd5f4348dfcc`
- rebase 映射：`649731ad -> a0fc877e`
- Native source：`729c5b260f68348f6889f4d0124d19fe5abb28d9`
- DLL SHA-256：`28FC55A50B839E49EC25F66DE0E0AA2D77E1689E24D3919C8C9DF8A5A75EAE29`
- Injector SHA-256：`41F005683163CAFAFCFAA46BE75EB1BB6008E854F3377FC94B90A7451C2365C9`
- CK3：`1.19.0.6`；EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- 支持组合：标准封建、`xar_off`、`ordinary_campaign_succession`、no pact、当前冻结 DLC/mod/load order
- 集成方式：仅 rebase + fast-forward；没有 merge commit 或 force push
- 实现测试：`test_gameplay_bridge` normal `244/244`、optimized `244/244`；`git diff --check` GREEN

功能提交只修改：

- `ck3_autonomous_player/src/xar_autoplayer/strategy.py`
- `ck3_autonomous_player/tests/unit/test_gameplay_bridge.py`
- `docs/ck3-native-ai/player-counterpolicy.md`

没有 native ABI、schema、MCP、open_kaishek 或能力广告变化。

## R866-R868 真实进展

### R866：接触时间线 GREEN

- 从 h1179 冷恢复，20/20 turns，+13 游戏日。
- 九次 fresh stationary contact-horizon query，八次 proof-bound advance。
- h1211/date `53281320`：checkpoint `65063326...C874`。
- report `EEB33B41...4403`（完整值以 artifact 为准）；进程完全回收。

### R867：真实战斗后 native-rally RED

- 从 h1211 冷恢复，79/80 turns，+46 游戏日。
- 两次 unavoidable-current contact transition，三次 battle-control query，三次 battle decision epoch；Army234881216 在真实战斗 terminal 后消失。
- 一次新的 `raise-troops-default` 生成 Army184549472；下一 turn 独立消费 `gathering -> regular`，位置 Province8750。
- h1340/date `53282424`：checkpoint `BE4E0C73...13C5A`，driver `B9815925...A51EA`。
- turn80 没有提交命令；RED 是 capital-only hold 没有接住已确认 native rally 的严格分支。

### R868：native-rally 修复 GREEN

- Artifact：`C:\ck3_mod_rewrite_process_assets\g2-ordinary-r868-h1340-native-rally-a0fc877e-20260918`
- 3/3 turns，248.283 秒；一条 fresh termination query + 两条 gameplay。
- turns2-3 均为 `native_war_defender_native_rally_hold_progress -> life-advance`，每次严格推进 1 游戏日并取得独立 paused postcondition：`53282424 -> 53282448 -> 53282472`。
- Army184549472 全程保持 regular、stationary、route-free、Province8750；WarID150994969 仍 active，score -50。
- 重复 raise、move、disband、declaration、terminal、旧 Army234881216 action 均为 0。
- report SHA-256：`52B6F95CC331CB70CB40A19EA8A891AB42264BC53CC32973886CBED838EDA430`
- operator receipt SHA-256：`2A4E5E2631DBA1EB8ED17FF17BDAAA44DE5AC5784940FAAC32083CC2E9E058B8`
- close seal SHA-256：`573A0B297C95F6087C2FA18C8C134701638072F459E1D94254A89DAE56370E6B`
- 新 h1347 checkpoint：`A3AB0B3E340BD7EF64A8DC7FBF1ED6CBE63379C179018D525C492170DEB564EC`
- 新 driver：`7339B8DDFEF1AED0E15C406B15CD0A82082D0014342411ACD0ABC67B5215DF47`
- PID115176、injector、stop file 均已清理；受管 CK3 进程库存为 0。

注意：formal report 只序列化通用的 phase/step/reason，没有把内部 `native_rally_hold_binding` 对象写进 report。该 phase 在代码中只能通过 durable raise + WarID/ArmyID/owner/province + restore ancestry 门到达，且完整矩阵已由 244/244 测试覆盖；不要把它写成“独立 live receipt 对象已经发布”。

## 下一恢复点

下一位负责人只使用 R868 h1347 pair：

- checkpoint：`C:\ck3_mod_rewrite_process_assets\g2-ordinary-r868-h1340-native-rally-a0fc877e-20260918\state\profile\save games\xar_checkpoint.ck3`
- driver：`C:\ck3_mod_rewrite_process_assets\g2-ordinary-r868-h1340-native-rally-a0fc877e-20260918\state\native-session\driver-state.json`
- history/date：`1347 / 53282472`
- actor/episode：`31853 / native-31853-af642d76cb41`
- 已确认生效：WarID150994969、Army184549472、rally Province8750、h1337 raise、两次 rally hold
- prior unconfirmed action：`null`
- 严禁：重复 raise、盲目 move 到敌占 capital45、复用旧 termination query 提交终局、对旧 Army234881216 发动作

h1347 尚未由第二个 CK3 进程 cold restore。若继续普通战役，下一轮必须单调分配为 R869 或更高，先盘点全局 CK3/injector 为 0，再用正式 operator 新进程恢复；不要在 R868 artifact 内原位续写。

## 下一项用户交付

源码侧修复已 GREEN，因此下一项最直接的用户价值是刷新冻结预览 ZIP。不要新增长跑；沿用现有 exact-ZIP 三轮资格门：

1. 从最终 master 和 h1347 pair 构建 deterministic stage/ZIP，并在全新目录解压。
2. fresh-extraction eligibility GREEN。
3. 正式入口产生真实非空 typed action、独立物质后置、下一 turn 消费。
4. `request-stop` 得到 checkpointed controlled stop。
5. 完全回收后，以不同 PID cold restore 同一 pair，继续同一高层目标且不重复动作。
6. 单实例清理和 11 项 promotion gate 全部 GREEN 后，才生成外部 GO receipt 并替换推荐下载。

若 exact ZIP 场景未在有界窗口产生非空动作，诚实记为资格证据不足；不要把 R868 源码侧 hold GREEN 冒充包内非空动作门，也不要下架 R802。

## 仍然开放的权威门

- G2：`1/8`，仅 M1 完成。
- GEN-034：`3/4`；D 仍缺 matching creation-time source capture 与固定六项 source-bound certificate。
- Council：`1/4`；guest、candidate-pending、replacement-fireability 仍开放，公共 query/action/ad 保持 OFF。
- `tgp_travel_events.0030`、`death_management.1007` 自然门未完成。
- 同 campaign 自然继承、继承人 gameplay、继承后 cold restore 未完成。
- 100 游戏年、首条 1066→1453、第二独立种子均未完成。
- 和平治理、家庭外交联合调度及 M6/M7 广度仍按权威合同开放。

`fervor.1002` 只有静态 direct consumer，没有 post-fix 自然 live；继续保持未广告。

## Git / 进程 / 清理状态

- 功能 tip `a0fc877e` 已在远端 master。
- `codex/war-r867-native-rally-hold` 远端分支、本地分支和 `C:\workspace\g2-war-r867-native-rally-hold-20260918` worktree 已删除。
- 当前集成 clone：`C:\workspace\g2-war-r794-no-safe-exit-20260917`。
- 共享 `Z:\ck3_mod_rewrite` 有用户历史改动；不要 reset、clean 或覆盖。
- 当前 CK3/injector 实例：0；R868 已 closed GREEN；R869 未分配。
- 本轮 WAR-R867-B0 临时远端/本地分支和 worktree 已清理；历史或其他工作包的 refs/worktrees 未纳入本次清理。当前没有仍占用 CK3 的 worker。

## 推荐读取顺序

1. 本文。
2. [`../autonomous-agent-progress/g2-requirements-v1.json`](../autonomous-agent-progress/g2-requirements-v1.json)。
3. [`../autonomous-agent-progress/daily/2026-09-18.md`](../autonomous-agent-progress/daily/2026-09-18.md) 与 [`../autonomous-agent-progress/weekly/2026-W38.md`](../autonomous-agent-progress/weekly/2026-W38.md)。
4. [`../ck3-native-ai/player-counterpolicy.md`](../ck3-native-ai/player-counterpolicy.md)。
5. R867/R868 formal report、operator receipt、close seal 与 singleton round ledger。
6. [`../ck3-native-ai/g2-preview-release.md`](../ck3-native-ai/g2-preview-release.md) 和现有 package builder/tests。
