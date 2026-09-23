# G2 自动游玩：2026-09-24 模拟试用交接

本页是本轮收口快照。用户在 2026-09-24 明确要求：**现有不完美战斗模型要在有界场景投入使用，并用真实结果持续拟合；完成在途工作、commit/push、停止开新工作，然后交接。** 不要把完整 exact 模拟当成唯一开工条件，也不要把研究模型的条件胜率误报为已校准真实胜率。后续新工作须由接班人按自己的授权启动。本页不替代 [G2 合同](g2-requirements-v1.json)、[现行状态投影](../project-state/current-state.json)、[当日日报](daily/2026-09-24.md)及冻结实机证据。

## 用户当前可获得的版本与边界

- **PRV008 窄范围 GO 保持不变。** 原 ZIP `Z:\ck3_mod_rewrite_process_assets\g2-preview-ordinary-ca852d1-20260922\release\g2-preview-ordinary-h1662-ca852d1-prv008.zip`，SHA-256 `B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3`；启动、状态、受控停止、冷恢复只从 `Z:\ck3_mod_rewrite_process_assets\g2-preview-prv008-frozen-path-live-20260922\START-HERE.txt` 读取，资格见同目录 `QUALIFICATION.json`。必需配对运行资产 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR` 保留。Z 路径仅是本机定位，跨机须用获授权路径映射重新核实。ZIP 不含 CK3。
- PRV008 仅 CK3 `1.19.0.6-steam23530548`、EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`、智能体 `ca852d1d5b368d951a392928907c642e6b325b3c`、DLL SHA-256 `B114FD8E13AF6518D623A60E7264807D882E4F4A640AF7840F60BA3F00029FA8`、`mod/xar_autoplayer.mod` 单 mod、`ordinary_campaign_succession/xar_off` 标准封建的原冻结窗口。旧 R0119 60/60、R0120 停止配对、R0121 新 PID 冷恢复 20/20 的资格未被本轮覆盖；不外推到任意存档、无限无人值守、完整 1066→1453 或双种子。
- G2 仍 **3/8**：M0/M1/M3 complete，M2/M4 in progress，M5–M7 not started。Robert 正式主线最近有效 h2134/raw53215920，持久 **2,983/36,524 游戏日**；百年门 **0/1**，首整局 **0/1**，独立种子 **0/2**。旧 Murchad 线、R0157/R0203 研究重放日期均不与 Robert 持久日期相加。禁止换算整体百分比。

## 本轮完成的实机与模拟事实

| 项目 | 已观察到的结果 | 限制 |
| --- | --- | --- |
| R0217 原版主 tick | 从原 R0203 配对只读 +24 小时、七原生边界，R14 双侧读回；#238 修复出伤逐次截断顺序，当前 master 双侧 outgoing 零残差 | 单空效果 tick，非整场胜率 |
| R0218 / R0219 | 前者输出目录预建导致 CK3 前 RED；后者真实 paused 首帧后一次性 runner 误读 v3 嵌套字段，日期/动作零，均保留 RED 并回收 | 不算主 tick 通过 |
| R0220 原版主 tick | 原 R0157 配对，动态分配 R0220，严格 +96 小时含三天 maneuver 与一个 main tick、零 typed；当前 master 的 R14 双侧、outgoing 双侧及 54 个 regiment 的 aggregate current/soft/hard 均与原版零残差。[冻结索引](Z:/ck3_mod_rewrite_process_assets/g2-combat-r0157-harness-v2-f67-no-launch-20260924/checks/R0220-MAIN-TICK-FREEZE.json) SHA-256 `0068BC85457D8CB1A50FBAC0B2293B04C0DA27C0105B8F8A9068C07E30731D6F` | 空 BattleEvent/scheduled knight tick；backing component、非空效果、多日 winner 未证，`win_probability_available=false` |
| R0188 研究模拟 | Robert War16777231、假设固定接战 entry8752、玩家 2327/敌1488，4096/4096 条件研究胜利；master 修复出伤后复算仍 4096/4096 | phase events 关闭、动态 advantage/退却/未来参战者未闭合；Wilson 下界只反映抽样误差，不反映模型偏差；**不是已校准真实胜率** |
| R0221 Robert 终战只读 | h2134 官方 prepare/rebind/preflight 后唯一实例同帧读 War16777231 守方比分 -15；白和平与胜利不可用。投降 validator/对方接受均为真，但 de-jure 物质条款不可观测；零动作、零日期，受控 stop、进程/owner 零，allocator `completed-green`。[冻结索引](Z:/ck3_mod_rewrite_process_assets/g2-robert-war31-termination-readonly-R0221-20260924/R0221-RAW-FREEZE.json) SHA-256 `BE7CCFF4DED6305744D3C2EE0ADD7FFD8D9163E0B662F02C3986090271DC30C5` | 不能盲投降；此读回不解除 War31 战争 RED |

旧 R0118 的 `native_war_no_safe_exact_route/planner_blocked` 仍独立 RED：354 对 747，旧承诺次日接触危险，具体投降条款未读。不要用 Robert 的 R0221 或 PRV008 替代此场景的闭环；原 h1566 save/driver 与官方恢复边界继续按 [前次交接](2026-09-22-g2-holiday-handoff.md)保护。

## 模拟试用和当前工作包

现有直接固定 `2×` 宣战/援围放行已从正式策略删除；PR #242 已把现役守方有界模拟试用入口合入 master，自动宣战仍 `forecast_required` / OFF。用户授权的是**有界试用**，不是把 R0188 `4096/4096` 改名成真实 `p_win=1.0`。Robert War31 的 R0207 同帧路线从省2610到敌围省2628，经 `[2614,2618,2617,2632,2613,8752,2628]`，到达目标约需46游戏日；首日原生 contact horizon 空，但今天的研究模拟不能证明46日后敌军仍在原位。试用路径必须在真实新帧重算接战输入，允许模型随战果修正，不用兵力倍率取代模拟。

`COMBAT-PROVISIONAL-DEFENSE-CANARY-B0` 由 `/root/combat_damage_boundary` 在独立 Z worktree `Z:\ck3_mod_rewrite\.task-tmp\COMBAT-PROVISIONAL-DEFENSE-CANARY-B0\work`、branch `feature/combat-provisional-defense-canary-b0` 实施；原 tip `08f7b2d` rebase 到 master `63800f4` 后，PR #242 final tip `d8cb86f4c66de00cca7ada3c4d9ac6e89451a0e5`。代码已把**现有**研究模拟接到正式守方解围入口：从同一 paused v3 计算 512 次有条件战斗，按模型内胜局下界、p90 永久损失、溃灭与人物死亡预算判断，**不读取固定2倍兵力阈值**。长路线只准在独立首站路线预览和次日无接触证明后提交首站 typed move；真正接敌必须在新的同帧路线、敌我编成和模型读回下重新判断，并先比较可读条款的安全停战出口。R0207 真实只读帧 2327:1488（约1.56倍）的离线重算是 512/512 个**模型内**胜局、Wilson 下界 `0.992553`、p90 永久损失约143人、预算约465人；这支持考虑首段，**不证明真实胜率、46天后敌军位置或实机动作成功**。normal/`-O` 聚焦测试各4/4，含低于2倍时选首段 typed move、即时同帧接敌与超预算拒绝；本轮依用户收口指令不新开 CK3 轮次，所以 typed/后置/下一 turn 仍待接班人有界验证。PR #242 的 CLA、签名和双 static 全 PASS，普通 FF 入远端 master `d8cb86f4c66de00cca7ada3c4d9ac6e89451a0e5`，GitHub 状态 MERGED，远端/本地 feature branch 与源码 worktree 已按 exact tip 核验清理。

宣战前 R0151 和当前 War31 不能混用。R0151 和平帧有19个 final-legal，其中目标33621 的唯一玩家单郡 `claim_cb`；但 `player_armies=[]`，原 #236 只见已集结军。PR #241 私有/OFF 补双方默认集结省份，**仍缺**假设征召后的 regiment/骑士/统帅、合法性、集结时间及到目标首接触；不因默认集结省份已读就启用自动宣战。

PR #242 原 tip 完整值为 `08f7b2d946dcc2115d985e0c53831594f5309fe6`；rebase 后 strategy、聚焦测试、player-counterpolicy、primary-defensive-war-response 四个 blob 分别仍是 `63e4d933ca9078656559f452a4e4643bf1284637`、`9d48b045902cc100b3bf8674cd1bd21ec185ef59`、`0b0b6e7ac8c5eb8c753f453eb3b6809eeb5af31d`、`30ff130157ba00b2dbc35c356907b6f9addd6bf9`。这些是静态内容身份，不代表实机通过。

## Git、资源与交接动作

| 工作包／缺口 | 本轮负责人、资源与真实状态 | 本轮证据／阻塞 | Git 与源码清理 |
| --- | --- | --- | --- |
| `WAR-PREWAR-HYPOTHETICAL-ROSTER-B1`／宣战前观测 | 独立 worker 已完成，未占 CK3 | 私有/OFF 默认集结省份读口；假设征召后 roster、合法性与首接触仍缺，不能宣布模拟宣战已可用 | PR #241 protected PASS，FF master `63800f4`，远端／本地 feature 与源码 worktree 已清 |
| `COMBAT-PROVISIONAL-DEFENSE-CANARY-B0`／现役战争有界试用 | 独立 worker 已提交，未占 CK3 | 静态聚焦 normal/`-O` 各4/4；R0207 同帧输入离线 512 次。尚无 typed、独立后置或下一 turn | PR #242 final tip `d8cb86f`，protected PASS、FF master、MERGED、源码 refs/worktree 已清 |
| `COMBAT-WINNER-ONLY-B0`／旧研究草稿 | worker 已结束；无 CK3 | 仅重投影旧模拟，obsolete/unqualified；归档原件 | 未 push；隔离源码 worktree／本地 branch 已清，远端无 branch |
| 本交接／状态口径 | 协调者编制本交接、日报和周报；未占 CK3 | PRV008 SHA 与三个配套路径存在；本机受管游戏进程清单为空。原 R0118 与 Robert War31 的 RED 均未关闭 | 本文最终提交、集成和源码清理身份以远端 master 日志和本轮最终交付记录核验，不预填自身 SHA |

平台给出最多 7 个 agent 槽位；在途代码 worker 已交付并退出，现仅协调者收尾，其他 agent 已完成或未启动，不把它们算作活动 worker。用户要求只收尾、不新开工作和 CK3 轮次，因此当前实机队列为空；R0221 受控停止、进程及 owner 回收已证，下一轮编号必须由持久分配器重新分配。

- 2026-09-24 当日日报 PR #239 已经 protected PASS、普通 FF 入远端 master `32043891306e40226346aa466c7fc5f1a4f69636`，原 feature 远端/本地 branch 与源码 worktree 已按相同 tip 核验清理。PR #240 是 R0220 原生树证据，原 tip `19126a4e9a3cbd52474c1bab896b51e59ff76768` 经 rebase 成 `2d48c24fb5bbe565727d465489e745968c1eba24`，受影响文档 blob `dd4e8f21328b5bea2079bd6c56653e881c0513f6` 未变；protected PASS、普通 FF 入远端 master `2d48c24`，远端/本地 feature branch 与源码 worktree 已核对清理。PR #241 为私有 default muster 读口，原 tip `2bb1f9071d25d6a63dc38269c0d931b871b19887` 先 rebase 成 `113b84056a3e8e86de0bc363b0a83daa2c9d5966`，再随 master 更新成 `63800f4af270a33afdcd30a9e08ac959d473f53e`，10 个受影响文件 blob 两次 rebase 后均未变；normal/`-O` 各10/10、Debug/Release native fixture 及最终 protected checks 通过，普通 FF 入远端 master `63800f4`，GitHub PR 状态 `MERGED`，该 feature 远端/本地 branch 与源码 worktree 已核 tip 清理。私有读口仍 OFF，无实机读回。
- PR #242 原 tip `08f7b2d946dcc2115d985e0c53831594f5309fe6` → 最终 `d8cb86f4c66de00cca7ada3c4d9ac6e89451a0e5`，4 个受影响文件 blob 恒定；CLA/签名/双 static 全 PASS、normal/`-O` 各4/4，普通 FF master、PR MERGED，远端/本地 feature 和隔离源码 worktree 已清。模型仅静态接线，实机动作与后置仍待。
- R0220、R0221、R0188、R0207 与 PRV008 原始配对和冻结索引均为运行/证据资产，保留；源码工作树集成后清理。R0215 后置 driver 虽合法配对，checkpoint anchor 仍是原 tick 前 raw53192376，+24 只有未保存尾部，不能当新日期来源；只读 audit `Z:\ck3_mod_rewrite_process_assets\g2-combat-natural-knight-event-r0215-post-20260924\checks\SOURCE-PAIR-AUDIT.json`。`COMBAT-WINNER-ONLY-B0` 未提交草稿仅重投影旧 4096 次，未提供新能力，已归档为 obsolete/unqualified 的 `Z:\ck3_mod_rewrite_process_assets\g2-combat-winner-only-abandoned-draft-20260924\MANIFEST.json`（SHA-256 `249B643FEFE433518152CE5199CD9F0EE48975EA2CD5B0FFE10595233D563C5E`）；隔离源码 worktree、本地分支已核验清理，远端从无该分支。R0188 研究重放材料作为证据保留，不当作可用胜率。
- 用户已要求本轮不再新开工作。接班前完成在途提交、受保护检查、rebase-only FF master、按 exact tip 清理源码 feature/worktree，保留上述运行资产；网络/权限/工具拒绝须逐项写明而非报告 DONE。所有新 Windows temp/cache/build/worktree 仅用实际非 C 盘。现有 #221 worktree 缓存与 #225 空目录清理曾受工具策略拒绝，不能换工具绕过。
- 接班人重新核验真实远端 master、全部受管 CK3/injector/operator/watchdog、owner/残树、EXE/DLL、官方 save/driver/profile 和持久 allocator。R0221 结束时本机进程/owner 为0是历史快照，不是下一轮启动凭据。当前无新轮次待启动。`open_kaishek` 仍无已证明需同步的破坏性公共接口改变；私有读口 OFF。

## 接班后首先确认

1. 核对本页最终 Git 映射、剩余临时源码 branch/worktree 和试用代码实际 gate；若仅静态/候选，不称已有生产动作。
2. 以 Robert h2134 原配对和 R0221 已知终战结果为起点，按单实例/官方恢复规则拿新同帧 route/contact/v3；若试用代码已经满足本轮合同，再有界提交至多一个动作并独立核 route、下一 turn 与 checkpoint。不要从 R0221 只读尾直接物理强配，也不要沿 R0118 旧危险承诺盲推。
3. 用自然战斗结果比较模拟与原版，优先修真正影响 winner 的 loaded phase effect、动态 advantage、参战者/退却；若预测失准立刻停止相同输入的主动接战并修正模型。研究试用和正式可推广能力分别记账。

本页的交接状态以最后实际集成及清理核验为准；不因文档写成而自动视为任务已完成。
