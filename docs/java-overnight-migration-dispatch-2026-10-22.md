# 今晚 Java 迁移：有限范围冻结收口（原56线调度）

休假交接入口：[2026-10-22 Java迁移与长局交接](handover/2026-10-22-java-migration-stabilization-vacation-handoff.md)。所有实现、采样和构建已按用户指令停止，本页后文的自主续项/并发安排只作历史，不能据此自动续工或新增范围。

**当前调度已于 2026-10-22 转为冻结收口。** 用户最新要求：“先别开新的迁移任务了，把这些现在正在跑的给我平稳落地。”立即停止新增迁移项、package 和自然后继领取；下文的自主续项许可暂停，56 数量目标不再驱动扩项。只收尾已经实际开始编写的有限组件，继续其采样、完整 Java 编译/JUnit、真实生产者到全部消费者闭环、实际接管与 RED 修复。仅列入候选但未写代码的项目取消，等待不计活跃实现。域负责人汇总现有 wave2/wave3/staging/D 草稿及未完依赖，Root 分批整合，不等待所有模块同时完成才实测。

首批已验证九模块及独立构建工具已合入并推送 `master`：`8722c3cf0194ee24c716a4214e6de17fb5e358d6`。九模块为 458 项 JUnit 通过，工具为 22 项通过，map 全消费者 CI 实测通过；后续 tools20 为 23 项通过。新增十七模块 java10 整图真实 RED：恢复与补员各 11/8 项通过，军事实际编译并执行 393 项但存在失败，admission 因弃用 API 与 `-Werror` 编译失败，runtime 因依赖失败未编译；当前树变更后须重新冻结验证。以上均不计新增游戏保存日；原件绑定 `machine_id: xenoamess-full-tower-eb9d2c1186` 与本机 `D:/codex-ck3-demos/2026-10-22-java-phase1/logs/build-java10.json`，14:57:09.049Z，不能外推其他机器。

用户最新要求：2026-10-22 今晚以 **56 条活跃迁移实现线为原则目标**，并明确不得为了数量强行拆分或凑任务。构建、采样、审查、Root不计入实现数；不把completed、只等待或只读review计为活跃。按自然组件和真实依赖选择独立工作，真实整合优先于空占并发。下表是候选明确所有权；无活跃调用的旧叶在同调用链改选实际组件，跨表占用先协调。旧32叶仍由原owner修整合故障，已纳reactor的源码在Maven运行时冻结；新工作写独立wave2目录，不污染当前来源闭包。

## 所有实现线共同执行约束
- 先读根AGENTS、docs/java-next-generation-architecture-2026-10-22.md与实际旧producer、全部consumer和已有tests。新模块/实现全Java21；范围内不另写Python业务。Maven默认命令mvn且版本>=3.10.0，无固定安装路径。
- 表中模块为java/ck3-control/wave2-{domain}；独占package org.xar.ck3.control.wave2.{domain}.{leaf}，相同test包、resources/{leaf}/与MIGRATION-{leaf}.md。父POM由Root拥有，wave2尚未入parent；域POM由下述唯一负责人维护，不要改父POM/共享contracts/其他包/冻结runtime SDK。不自动创建新子agent，留团队余量给集成。
- 提交真实可编译Java实现、不可变强类型模型与集中strict入口。保留原Decimal/Fraction/原生位宽/空值语义，实际拒bool/float/错误字段。处理raw浮点负例时直接送原token，避免JSON树把1.0改成1。旧SDK扩展容器做声明投影，不误套exact keys。
- 每leaf源码+样本初期<=160KiB；需要扩大先报告真实原输入/输出规模与有限估算，不放宽业务守卫。沿同一producer→全部consumer，默认JUnit用提交的真实原producer golden；golden须保来源SHA/时间/machine_id。纯接口不能用stub或输入GREEN布尔替身授来源/恢复/动作资格。
- 只迁真实纯叶或明确独立adapter；若源很大，选择完整实际依赖闭包并列未迁范围，不翻译成巨类。发现仅历史attempt/无活跃调用，先向Root报告并选活跃可复用边界。domain不导入adapter，不每函数建HTTP或JVM。
- 不启动Game/Steam/Task/RPC、不写canonical或pending，不直连第二native pipe。新Game与writer由Root唯一持有。N46旧Game已关闭，原11558 UNKNOWN不重放，保存仍5628/10950。
- Maven唯一writer/root/g2_m7；golden/Java执行统一交/root/storage_resume调度，使用合格Java Win32 Job，每个capture默认整树512MiB。不私起56个JVM，不自行mvn/下载。Root依据本机新鲜RAM实测另行释放有限多worker时，严格按其联合上限运行；构建中仅向D写采样输出，冻结Z资源须等完整构建终态后导入。
- 临时/依赖/构建仅D:/codex-ck3-demos/2026-10-22-java-phase1。实际有限release02 review20:00Z，D4GiB/Z32MiB同池不新增take；未获后续manualreview不可自动续。所有exec用cmd.exe/login:false，禁PowerShell，避免shell管道/重定向截断文件。Git/公共POM只Root写。
- 完成当前组件后明确SOURCE_READY并通知Root/M7冻结范围；在同一自然调用链核对未占用的后续组件后，可自主继续并通知域负责人/Root，无需例行等待确认。收到完整构建RED优先修本人原包（先确认该attempt已结束）。确实缺少独立工作或需要依赖时如实报告，不为在线数量造空模块、拆小任务或把等待算实现。
- 目标20–30分钟给第一版源码，继续真实差分和消费者adapter整合，不以源码量、测试数、并发数代替游戏/性能成果。Root持续分批合并验证已完成项。

## 具体分派

wave2域唯一协调/POM负责人：finance=`decision_gaps`，governance=`java_education`，military=`java_declaration_priority`，planning=`java_opportunity_selector`，events=`java_mandatory_choice`，runtime=`native_clock_failure_java_bridge`，development=`wave2_construction_scene`，prisoners=`wave2_release_preview`。负责人仍做实现，协调同域调用链、所有权和真实依赖；可以在未纳当前reactor的域POM添加已核实依赖，不形成循环，不修改父POM。具体同域纯叶替换与下一自然组件直接协调后执行，无需Root逐条确认。实际执行继续由storage/M7统一，源码进父graph和Git只Root操作。每批设有限冻结范围，后继自然组件进入wave3或独立staging目录，不能持续改同一来源闭包而延后实测。
| # | owner | domain / leaf | 当前真实源或接口边界 |
| --- | --- | --- | --- |
| 1 | /root/decision_gaps | finance/warcash | ck3_autonomous_player/src/xar_autoplayer/m5_war_cash_resource_v1.py |
| 2 | /root/throughput_audit | planning/scoretarget | ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py |
| 3 | /root/java_replenishment | military/landstock | ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_land_stock_supply_budget_projection.py |
| 4 | /root/cold_resume_readiness | runtime/savedproof | Original SDK current-SAVE verifier / existing current_saved_basis_v1.py measurement entry |
| 5 | /root/native_clock_failure_java_bridge | runtime/clockreader | Existing same-Session STATUS/SEM transport and late-outcome application reader |
| 6 | /root/java_faction_gift | finance/factionthreat | ck3_autonomous_player/src/xar_autoplayer/faction_threat_response_inputs_v1.py |
| 7 | /root/java_feast_budget | finance/giftwarcash | ck3_autonomous_player/src/xar_autoplayer/faction_gift_wartime_cash_v1.py |
| 8 | /root/java_feast_value | finance/feastordinary | ck3_autonomous_player/src/xar_autoplayer/activity_feast_ordinary_v1.py |
| 9 | /root/java_joint_budget | planning/jointshortlist | ck3_autonomous_player/src/xar_autoplayer/m5_joint_shortlist.py |
| 10 | /root/java_crown_authority | governance/government | ck3_autonomous_player/src/xar_autoplayer/ordinary_campaign_government_context_v1.py |
| 11 | /root/java_education | governance/educationneeds | ck3_autonomous_player/src/xar_autoplayer/family_education_needs_12004.py |
| 12 | /root/java_marriage | governance/betrothal | ck3_autonomous_player/src/xar_autoplayer/current_betrothal_fulfillment_proposal.py |
| 13 | /root/java_heir_preference | governance/heirlineage | ck3_autonomous_player/src/xar_autoplayer/first_heir_native_lineage_policy.py |
| 14 | /root/java_lifestyle_min | governance/focusscope | ck3_autonomous_player/src/xar_autoplayer/lifestyle_education_focus_scope_v1.py |
| 15 | /root/java_lifestyle_perks | governance/educationpreference | ck3_autonomous_player/src/xar_autoplayer/family_education_request_preference_12004.py |
| 16 | /root/java_mandatory_choice | events/choiceplanning | ck3_autonomous_player/src/xar_autoplayer/mandatory_choice_planning_v1.py |
| 17 | /root/java_interaction_fallback | events/interactionregistry | ck3_autonomous_player/src/xar_autoplayer/pending_interaction_source_registry.py |
| 18 | /root/java_vanilla_event_policy | events/eventoutcome | ck3_autonomous_player/src/xar_autoplayer/vanilla_events/outcome.py |
| 19 | /root/java_declaration_priority | military/prewaradmission | ck3_autonomous_player/src/xar_autoplayer/ordinary_prewar_force_admission_v2.py |
| 20 | /root/java_defender_risk | military/exitcomparison | ck3_autonomous_player/src/xar_autoplayer/formal_defender_exit_comparison.py |
| 21 | /root/java_projected_contact | military/armyinventory | ck3_autonomous_player/src/xar_autoplayer/physical_army_inventory_v1.py |
| 22 | /root/java_battle_retreat | military/realmsiege | ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py |
| 23 | /root/java_optional_cadence | planning/warcashprovenance | ck3_autonomous_player/src/xar_autoplayer/war_cash_floor_policy_provenance_v1.py |
| 24 | /root/java_campaign_cadence | planning/scoreinputs | ck3_autonomous_player/src/xar_autoplayer/campaign_score_existing_inputs_v1.py |
| 25 | /root/java_war_query_cadence | military/warresults | ck3_autonomous_player/src/xar_autoplayer/ordinary_war_results_window_v1.py |
| 26 | /root/java_opportunity_selector | planning/jointintake | ck3_autonomous_player/src/xar_autoplayer/m5_joint_intake.py |
| 27 | /root/java_sway_reuse | planning/swaylifecycle | ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_lifecycle_observation_v1.py |
| 28 | /root/java_cold_admission_contract | runtime/providerchain | tools/g2_saved_campaign/canonical_native_provider_chain_v1.py |
| 29 | /root/java_owner_prepare | runtime/stdioidentity | tools/g2_saved_campaign/mcp_owned_stdio_binding_v1.py |
| 30 | /root/java_full_batch_timing | runtime/performancewindows | tools/g2_saved_campaign/summarize_performance_windows_v1.py |
| 31 | /root/java_deadline_credit | runtime/deadlinetransport | ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_deadline_transport_v1.py |
| 32 | /root/resume_path_review | runtime/closedadoption | Current closed-partial basis admission and original writer adapter integration |
| 33 | /root/wave2_gift_outcome | finance/giftoutcome | ck3_autonomous_player/src/xar_autoplayer/faction_gift_outcome_v1.py |
| 34 | /root/wave2_gift_pending | finance/giftpending | ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py |
| 35 | /root/wave2_construction_intent | development/constructionintent | ck3_autonomous_player/src/xar_autoplayer/construction_selected_intent_continuity_v1.py |
| 36 | /root/wave2_construction_scene | development/constructionscene | ck3_autonomous_player/src/xar_autoplayer/construction_scene_scope_v1.py |
| 37 | /root/wave2_construction_economy | development/constructioneconomy | ck3_autonomous_player/src/xar_autoplayer/construction_economic_outcome_v1.py |
| 38 | /root/wave2_army_selector | military/armyselector | ck3_autonomous_player/src/xar_autoplayer/current_replenishment_army_selector_v1.py |
| 39 | /root/wave2_stock_supply | military/stocksupply | ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_stock_supply_budget_projection.py |
| 40 | /root/wave2_fleet_supply | military/fleetsupply | ck3_autonomous_player/src/xar_autoplayer/bridge/army_next_fleet_supply_budget_projection.py |
| 41 | /root/wave2_monthly_loss | military/monthlyloss | ck3_autonomous_player/src/xar_autoplayer/bridge/army_monthly_loss_budget_projection.py |
| 42 | /root/wave2_supply_schedule | military/supplyschedule | ck3_autonomous_player/src/xar_autoplayer/bridge/army_future_daily_supply_schedule_contract.py |
| 43 | /root/wave2_army_queue | military/armyqueue | ck3_autonomous_player/src/xar_autoplayer/bridge/army_daily_queue_inputs_contract.py |
| 44 | /root/wave2_county_entry | military/countyentry | ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_inputs_contract.py |
| 45 | /root/wave2_disembark | military/disembark | ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_disembark_penalty_contract.py |
| 46 | /root/wave2_combat_roles | military/combatroles | ck3_autonomous_player/src/xar_autoplayer/bridge/army_current_combat_roles_phase_inputs_contract.py |
| 47 | /root/wave2_war_exit_terms | military/warexitterms | ck3_autonomous_player/src/xar_autoplayer/bridge/war_exit_terms_contract.py |
| 48 | /root/wave2_coalition | military/coalition | ck3_autonomous_player/src/xar_autoplayer/bridge/prewar_force_coalition_v2_contract.py |
| 49 | /root/wave2_player_risk | planning/playerrisk | ck3_autonomous_player/src/xar_autoplayer/ordinary_player_risk_context_v1.py |
| 50 | /root/wave2_succession | governance/succession | ck3_autonomous_player/src/xar_autoplayer/ordinary_succession_operating_context_v1.py |
| 51 | /root/wave2_marriage_handoff | governance/marriagehandoff | ck3_autonomous_player/src/xar_autoplayer/family_marriage_episode_handoff_v1.py |
| 52 | /root/wave2_release_preview | prisoners/releasepreview | ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_release_preview_contract_12003.py |
| 53 | /root/wave2_negotiated_preview | prisoners/negotiatedpreview | ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_negotiated_preview_contract_12003.py |
| 54 | /root/wave2_holy_loan | finance/holyloan | ck3_autonomous_player/src/xar_autoplayer/holy_order_loan_decision_observation_v1.py |
| 55 | /root/wave2_holy_reinforcement | military/holyreinf | ck3_autonomous_player/src/xar_autoplayer/holy_order_siege_reinforcement_v1.py |
| 56 | /root/wave2_commander_quality | military/commander | ck3_autonomous_player/src/xar_autoplayer/commander_quality_formal_proposal_v1.py |

4/5/32为游戏恢复关键链：完成可执行的原SDK测量adapter、固定reader应用协调、原writer窄提交与新basis实际消费集成；它们与现有纯reducer协同，不能再只返回默认UNAVAILABLE而把接入当完成。实际读Driver/SAVE须与Root/采样owner约定一次测量、缓存原件身份与结果，避免重复大正文读取；仍不运行Game或改账本。SDK外部调用仅为已存在validator转运，业务与资格判定放Java。

本清单只是本晚执行调度，非永久无限并发或容量授权。版本/机器实测以小型实际回执为准；按record于2027-04-20归纳复核。
