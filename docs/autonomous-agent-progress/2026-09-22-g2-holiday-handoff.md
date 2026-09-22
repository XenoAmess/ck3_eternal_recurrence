# G2 自动游玩：2026-09-22 休假交接

本页是交接时点的增量快照，不替代 [G2 权威合同](g2-requirements-v1.json)、[现行状态投影](../project-state/current-state.json)或不可变实机证据。交接指令到达后未新开工作包、CK3 轮次或长跑；仅完成在途任务收尾、集成和记录。接班人应在自己的授权环境重新核对远端 master、单实例所有权及下述路径，不能把本机路径当作跨机器通用路径。

## 用户现在能使用什么

窄范围可运行预览已 GO：冻结 [PRV008 ZIP](<Z:/ck3_mod_rewrite_process_assets/g2-preview-ordinary-ca852d1-20260922/release/g2-preview-ordinary-h1662-ca852d1-prv008.zip>)，SHA-256 `B9952E544C78D51F650FCBF252D2DE81B1E005B0EA5081880AEE9FDECC2BD9F3`；[实际验证过的启动、受控停止、状态、冷恢复命令](<Z:/ck3_mod_rewrite_process_assets/g2-preview-prv008-frozen-path-live-20260922/START-HERE.txt>)及[资格证据](<Z:/ck3_mod_rewrite_process_assets/g2-preview-prv008-frozen-path-live-20260922/QUALIFICATION.json>)。ZIP 不含 CK3。本机附带 manifest/save/driver 位于 `Z:\ck3_mod_rewrite\.task-tmp\PRV008-FROZEN-EARLY-PAIR`，是**运行资产，不得当作临时 worktree 清理**。

受支持组合：CK3 `1.19.0.6-steam23530548`，冻结 EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；智能体 commit `ca852d1d5b368d951a392928907c642e6b325b3c`、DLL SHA-256 `B114FD8E13AF6518D623A60E7264807D882E4F4A640AF7840F60BA3F00029FA8`；仅加载 `mod/xar_autoplayer.mod`，`disabled_dlcs=[]`（观察到 29 个 DLC descriptor，授权状态未核实），`ordinary_campaign_succession`/`xar_off`/标准封建。R0119 正式 60/60 turn 含真实 typed 动作、独立后置及后续 turn 消费；R0120 受控停止形成配对 checkpoint；R0121 新 PID 从该对 checkpoint 冷恢复 20/20 且未重复动作，全部进程回收。资格仅针对 R0074 派生的普通封建 actor `31853`、episode `native-31853-af642d76cb41` 的有界窗口；本冻结路径未发生自然继承。**不是**任意普通存档、无限无人值守、完整 1066→1453 或双种子资格。遇到范围内未知阻塞状态应停止并保存 RED，不能手工代点。最新本机核验的受管 CK3/injector/operator/watchdog 为 0，唯一实例所有权已释放；启动前仍须重新检查所有受管环境。

## 权威进度与当前阻塞

| 门/能力 | 交接状态 | 证据或下一项必要动作 |
| --- | --- | --- |
| G2 合同 | `3/8`：M0/M1/M3 complete；M2/M4 in progress；M5–M7 not started。合同禁止换算整体百分比 | 不修改八项定义/分母，不把预览包当作新里程碑。 |
| 100 游戏年 | 持久日期 `9,482/36,524` 天，约 `25.96%` **仅为时间跨度**；阶段门 `0/1`，首整局 `0/1`，独立种子 `0/2` | 从最近有效配对 checkpoint 继续，不能把日期占比当成产品完成度。 |
| 战争持续运行 | R0117 路线修复聚焦复验 GREEN；R0118 `native_war_no_safe_exact_route`/`planner_blocked` RED | [R0118 证据](<Z:/ck3_mod_rewrite/.task-tmp/RUN-001/century-h1471-continuation/R0118-evidence-manifest.json>)。我军 354 人已承诺赴唯一目标/首都 45，敌军 747 人正围攻同省；次日接触不安全。白和不可用，守方投降具体头衔/封臣/资源条款不可读，旧完整预览曾两次崩溃，严禁盲投降或重复动作。h1566 存档之后的 RED driver 尾部须由官方恢复器裁切，不能物理强配。 |
| R0122 改道只读候选 | `completed-red`；preview/contact=0、动作=0、日期+0，进程树清理/owner 释放 | [R0122 清单](<Z:/ck3_mod_rewrite/.task-tmp/RUN-001/century-h1566-reroute-probe/R0122-evidence-manifest.json>) SHA-256 `0ED711EB…D0197`。首轮预启动 `xar_on` 与 prepared `xar_off` 冲突；同轮修正后 PID176888 在 pipe ingest 因 `persisted succession lifecycle differs from frozen run profile` 失败并超时。现保留的 h1566/raw53371896 配对 save SHA `F3BD2AB7D648044C5B3B9A1BD732D1480503183D97F6D02C7C406B9699933E3B`、driver SHA `9E0C9D9AF115B39F60D1991345FDA93F70DF54767AEBBBBD1D64B824360565C3` 未变。接班人若继续此候选，须在**新轮次前**从 prepared environment 显式绑定 `ordinary_campaign_succession/xar_off`，先通过 no-launch 配对检查；本轮没有安全改道结论。 |
| 议会 | 四门仅 already-councillor `1/4`；guest/pending/replacement 尚无自然阳性，public query/action/ad 均 OFF | R0102 总管空席不能代替后三门。等合法自然 paused 场景，以受控只读筛查再按既有合同验动作、独立 incumbent 后帧与下一 turn。 |
| 自然事件/继承 | M2 `.0110` 同角色合法性前后 readback 283→263，另有 15 天混杂、county modifier 未读，不能闭合独占因果；`.0030` exact 原版需 TGP/天朝政府，不可从标准封建首种子自然取得；`.1007` 尚无近邻配对场景。M3 已由旧 R0077 权威完成，但不能外推到预览冻结路径 | [M2 清单](<Z:/ck3_mod_rewrite_process_assets/m2-0110-bounded-live-20260922/EVIDENCE-MANIFEST.md>)；自然事件选项与物质结果继续依 exact-build 合同。 |
| M4 生活方式/治理 | 私有 focus/目标 XP/点数只读字段及 readback runner 已合入；尚无同版本实机读回、typed focus 选择或 perk 加点；不能广告或称治理两年闭环 | 原 R0112 prepared 状态带 live restore 尾，不能作新鲜源；接班人要重新配对 h1094，ordinary/xar_off prepare/rebind，绑定新 DLL SHA 前缀 `3778DBE7…9460` 与最终 runner，再申请唯一实例窗口。 |
| M5 家庭外交联合调度 | 657 个 distinct final-legal 私有候选只是合法性库存，缺同帧机会成本/长期承诺/战争预算联合选择；M5 未开始 | 不把复制/非法候选凑数，不用只读查询代替动作闭环。 |

## 接班顺序与时间风险

先保护预览运行资产和单实例规则；若继续战争，优先修 R0122 冻结生命周期绑定并作 no-launch 检查，随后再由新负责人按优先级申请唯一实机轮次。R0118 的物质条款/安全路线仍需 exact-build 最小只读观测，不能因 R0122 启动错误而降级忽略原战争 RED。议会合法场景、M2 自然事件、M4 只读读回和 M5 同帧选择器可在**不占 CK3**的开发/证据准备中分别推进；凡加载 DLL/游戏文件变动均须串行重启，不能热换当前运行文件。

原工程目标为 09-20 议会（已错过，1/4）、09-25 战争（R0118/R0122 风险）、09-30 自然事件/继承、10-08 治理、10-14 家庭外交、10-18 百年门、10-23 首条整局、11-06 第二独立种子，11-20 风险缓冲。它们不是开工日或新承诺。项目所有者预告约 09-30 游戏大更新和二进制变化；旧 `1.19.0.6` 必须继续冻结，升级另列 EXE/ABI 迁移与复验，不把智能体修复说成同一制品自始未变。当前无足够墙钟吞吐数据可重估交付日期。

## Git、资产与边界

PR #79 报告/M5 增量 `3db08ff→be63861`、`12926a1→c570592`；PR #80 守方投降条款缺口 `710055e→dc4554a`；PR #81 M4 私有目标读数 `b724c8b→1a8890d`；相关提交均经 rebase-only 到远端 master、受影响文件 blob 校验并清理临时远端/本地分支和 worktree。M4 runner 原提交 `1b706508e28ee3527346b26540d3f23802a376ba`，normal/`-O` 测试各 12/12；最终 PR/commit/清理结果见本页后续收口记录。交接报告本身同理须经受保护集成后才算 DONE。仓库根工作区有大量无关/历史脏状态，勿 reset 或覆盖。

本机任务临时根 `Z:\ck3_mod_rewrite\.task-tmp`，制品根 `Z:\ck3_mod_rewrite_process_assets`；所有新 temp/cache/build/clone/worktree 仍必须落在实际可写的非 C 盘，勿改 HOME/USERPROFILE。当前 `PRV008-FROZEN-EARLY-PAIR` 必留；M4 的 Z 盘候选/构建缓存待实机读回归属确认；R0118 的旧浅 clone `.task-tmp\WAR-R0118-EMBARKED\work` 仅 `.git`/缓存，删除曾被工具策略阻止，未绕过；其他早期工作树不在此次交接清理授权范围，须逐个核实归属/未提交内容/进程占用再清理。不得以“已在 Z 盘”为永久堆积理由。open_kaishek 当前没有已证明需同步的破坏性公共接口变化；新增私有读回未对外广告。MCP/原生事件资产继续按版本绑定复用，不将一次性 runner 当作通用能力已完成。

**值班纪律：** CK3 同时只准一例；新启动必须使用持久分配器递增轮次并先核旧进程。RED/超时/未执行/证据不足分别记账；ACK 不等于后置状态。只 rebase 集成，禁止 merge commit、强推共享 master。完成一项集成后立即核验原 tip→最终 blob、停止写入并清理对应临时远端/本地 branch/worktree；制品与 checkpoint 不随源码 worktree 删除。

## 收口记录

- 交接指令后未开启 R0123 或任何新工作包；R0122 由原负责人等到受控超时并完成 cleanup，CK3/injector/operator/watchdog=0。
- M4 runner 及本报告的最终 master 映射、临时 branch/worktree 清理状态在集成完成后补录；若受保护检查未完成，明确保留为“已推送、待集成”，不能称 DONE。
