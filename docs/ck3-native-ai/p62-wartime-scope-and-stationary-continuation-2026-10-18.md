# P62：战争目标范围、非目标驻军续行与战略增援

状态：**NOT_DEPLOYED**。本页记录已封实际输入与离线候选资格，不宣称 R6 已安装、推进、救援或雇佣成功；后续实际业务另附回执。machine_id：`xenoamess-full-tower-eb9d2c1186`。整理时间 `2026-10-17T23:01:59Z` 起；原回执实际 UTC、帧和完整 source SHA 见[小型证据索引](evidence/p62-wartime-scope-and-stationary-continuation-2026-10-18.json)。本轮没有 MCP、Game、Driver/SAVE 读写或 Native DLL 修改。

## 实际缺口：军费范围和行军目标被混写

R5 AUTO1039 在 `2026-10-17T22:50:19.585512Z` 至 `.643761Z` 返回 `blocked`，phase 为 `native_war_constructor_defense_unavailable`，selected step 为空。fresh SEM1040 与其同帧：`native10747/public420/raw53362224/conn16`，玩家40695仍存活且暂停。不是一次失败进攻或已经提交的行军。

| 已封观测范围 | 实际内容 |
|---|---|
| 己军 | public CUnit `167772577`，691兵，位于2624；regular、非战斗、非撤退 |
| 当前路线 | `move_target=null`，`route=[]`，读回 `complete_empty`；没有到2619的已提交路线 |
| 候选目标2619 | 敌 CUnit `285213101`，4073兵；当前围城也绑定此军 |
| 另一组敌军 | `402653372/436207707`，合603兵，位于2628 |
| 主导战争去重已观测敌军 | 三支共4676；未动员兵力、未来增援和实际胜率仍未知 |

旧私有 finance 文案取军费优先关注的一场战争，显示691/603，却接在 general 对2619的决策旁。603不能说明目标2619的敌人。跨范围混写会同时误导观众与后续分析；全局4676也不能代替每个具体目标的参战集合。

AUTO1035 的 H1 是**假想**2624→2619，候选 route `[2619]`、预计 `53362416` 抵达，即8天后；它仅证明当前情景下首日 `53362224..53362248` 无接触。它既未提交路线，也未证明8天安全。原 Native proof 要求实际路线/目标与证明一致，正确拒绝拿这份预览推动空路线驻军。

## 复用现成的当前位置 H1

SDK48 已有普通 stationary contact consumer（`strategy.py:14961–15068`）及 Native 对非目标驻军的当前位置查询投影（`native_driver.py:32450–32467`）。原 `_fresh_route_contact_advance_proofs` 同时核当前省、空路线、无移动目标、完整敌军集合、全己军范围和同帧身份；`_execute_route_contact_horizon_advance` 重新核 revision/proof 后才调用原 exact-one-day 时钟。

新候选 `nonobjective_stationary_contact_v2.py` SHA `87d27167739fd108db37d0ecd01685476f1ef12c25f8d048365e66ae2ab9d4fe` 仅在原 constructor unavailable、无动作的 general 入口补消费者。安装只包 `_general_battle_forecast_ingress`，保留原 choose/Service 别名、后处理和全部 Native admission。

1. 唯一可控己军确为当前玩家、regular 原地、无必须处理窗口时，选择现成只读 step：`query-route-contact-horizon-v1-167772577-to-2624-h-3-285213101-402653372-436207707`。目标是实际当前位置2624，三支敌军全部保留。
2. 只有新查询确实成功且原 Native 完整 proof 可用，才选对应 `advance-route-contact-horizon-v1-*`；最多原地一天，暂停重规划。plan 显式携带真实 `active_wars`，供既有结果分类器核全战争范围。
3. 缺 proof、过帧、移动/位置变化、范围不全或接触不明，仍保留原无动作诊断。没有伪造 objective、改移动命令、删远敌或授权接敌。

离线已完成3项测试、22项负例：实际1033/1035/1037小回执与SEM1040进入真实 general→原1859→新候选→`Service.plan_turn`，外层 ghost/CArmy guards 仍调用；核心 baseline 取自实际1039。首步正确选2624查询，旧2619预览不能授权推进。另一个**明确合成的未来2624原地 H1**通过真实 normalizer/Native proof 与 revision 分支，停在 exact-one-day 底层调用边界，零 IPC。它证明消费者及门禁兼容，不能算实际 Native 动作、R6全启动或最终分类器验收。

一天观察是避免非法军令的续行路径，尚未解决如何解除围城、保存领土或合理撤离的长期玩法问题；不能把每天原地等待算作战争智能已经完成。

## 显示候选只澄清范围

`finance_display_scope_v1.py` SHA `54b7e79ec0d4a84720652b36cb61f8565968de05b33fb38c586e6c6a1b819a84` 仅替换私有 finance 的 `_describe`，限定 `native_war_*` phase：分别写“军费关注战争ID/该战兵力”和“主导战争去重敌军”，明确前者不代表行军目标、头数不代表胜率。它不改 selected step、phase、attack flag、采购/预算或机器原始原因备份；非战争交给旧 formatter。

实际SEM1040与原私有 tradeoff/formatter 的1项离线测试通过，验证4676全局范围及业务字段不变。此候选尚未部署，也未修复采购模型本身。

## 战略雇佣：局部价值不能只看全场兵差

现模型要求出生省已有己军原地集结，并以全局去重人数反转筛采购，会忽略局部补员、守备轮换或释放另一军的价值。后续应保留全局军费风险账，同时按**真实目标成员**评局部边际价值、合同/现金预留、预计出生地和到达不确定性。ETA unknown、出生地没有现成己军不应成为永久采购禁令；用户正常战略风险授权继续有效，不增加审批门。

实际 `.4` 的 `BindMercenaryPositionImage12004` 以精确 EXE 身份绑定原生 selector `24A6A90`；已有迁移来源闭合 `2625ACF→24A6A90..24A6C5C`（460B）。[迁移账](mercenary-query-and-mode1-hire-migration-12004.md)与[选址研究](mercenary-hire-spawn-selection-12003.md)区分公司 home、默认征召地与有战争时的自动雇佣出生点；后者是 `.3` 来源知识，不能替代本机 `.4` 业务验收。当前 market 已发布预计出生省/ready/是否尝试及战争数，未发布每项原生安全过滤、rally/fallback 分支，更没有未购 CompanyID→CUnit/CArmy 的真实 route ETA。

有限决策可分两类：救急收益依赖赶上围城/战斗时，不能把未知到达写成必达；有预算与长期用途的战略备兵，可以明示承担未知，而非一律拒绝。保留原生 CanHire、当前报价、现金机会成本及单次未知动作不重试合同。买后分别核雇主、资金、新实际可控军队，再对该军读 preview/H1、实际路线和 reinforcement assignment；最后以到达、CombatID、损失、war/title 后验判定收益。

历史AUTO40的856兵/211金属于旧报价，不能与本帧691/4073拼成当前可执行采购。完整候选矩阵及来源索引 SHA 已收入本页证据；当前没有新报价或实际雇佣结果。Native25仍只以实际广告的V2能力为据，公共V3源码不代表本场可调用。旧 P60 的 constructor、584候选和首次自然 retreat 合同见[前一专题](p60-native-constructor-nohire-and-retreat-2026-10-18.md)，本页不增加 G2 或战果信用。

## 2026-10-18 追加：R6 实际续行与正常 SDK 退出

本节追加后续事实，保留上文 `23:01:59Z` 整理时的 **NOT_DEPLOYED** 状态。此次离线核对时间为 `2026-10-17T23:35:40Z`，machine_id 仍为 `xenoamess-full-tower-eb9d2c1186`；只读小型 Root 审阅、原生动作回执及既有 metadata，未读 Driver、SAVE、26,066,209B 的 SEM935 原件或媒体，新增实机调用为0。完整路径、字节数、SHA 与字段投影追加于同一[证据索引](evidence/p62-wartime-scope-and-stationary-continuation-2026-10-18.json)。

R6 在同一 Game `51028`、connection17 复用 SDK48；实际 bootstrap 绑定了上述 `87d27167…d4fe` 原地续行叶。AUTO33 于 `23:15:33.620106Z–23:15:35.144579Z` 实际选择 `advance-route-contact-horizon-v1-167772577-to-2624-h-3-285213101-402653372-436207707`，phase 为 `native_war_stationary_contact_horizon_progress`。其 proof 绑定当前位置2624、空路线和全部三支已观测敌军，Native exact-day clock 实际从 `53362224` 到 `53362248`，完成1个日 tick、overshoot0并读回暂停。它没有提交移动命令，也不证明解围、保地或取胜。

FULL16 实际结束25个普通周期，累计6718 cycles，raw 为 `53362296`；相对 MET15 的 `53362224` 共推进3天。AUTO33 的1天已经包含在这3天内，不能另加。MET68 于 `23:16:03.171892Z` 独立读回玩家40695存活、暂停、地图就绪、2场战争，以及相同结束 raw。Root 的 `ROOT-P50R6-POST-MODE-RESUME01.json` 为后续续行绑定了实际 SDK 代际、已结算状态和 source epoch；这些 metadata 修复本身没有新增业务或日期信用。

末次 AUTO934 于 `23:21:43.682038Z–23:21:44.635511Z` 返回 `native_war_general_battle_model_rejected`，selected step 为空。它有可用的假想2623→2619接触输入和 `estimated` bounded battle model，实际原因是 `bounded_model_risk_budget_exceeded`：256样本中玩家0胜，p90硬损失比0.468839、wipe概率0.0703125，超过配置0.25及0.05预算。这是当前模型下的风险拒绝，仍为 `research-only-bounded-core`、`native_parity=false`，不能把模型概率当作真实战果。候选2619绑定敌军 `285213101`；同帧 Root 审阅读回该敌4152兵、己军844兵。旧 finance 显示的844/595仍只指另一场军费关注范围，不能替代该目标兵力；本页的 formatter 候选至此仍未部署。

Root 的 SEM935 审阅（`23:31:46.982484Z–23:31:51.253528Z`）确认 `native10941/public195/raw53363736`，玩家仍存活、暂停、地图就绪。CLEAR936 于 `23:32:36.389038Z` 仅按这份 fresh frame 清除无动作阻塞，保留7140 completed cycles：原动作未重放，新增 MCP/native调用0、业务信用0。它不构成接敌、投降、授独立或推进一天。

最后 `ROOT-P50R6-OWNER-CLOSED.json` 实际观察 SDK queue222180 与 application157208 均 kernel exit0，launcher0、normal=true，`Game_stopped=false`、`recording_stopped=false`。该小回执未内置退出 UTC，本页只记录上述核对时间，不用文件 mtime 代造精确退出时刻。R6 的有限续行已从离线候选进入这次实际业务；显示修正、战略雇佣效果、最终保地、G2新增信用及后续 R7 成功均未由本节证明。
