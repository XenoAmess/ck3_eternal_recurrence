# P79：分散己军的安全会合候选

状态：`SOURCE_QUALIFIED_NOT_DEPLOYED`。`machine_id: xenoamess-full-tower-eb9d2c1186`；证据观察时间、实际回执 UTC、完整 SHA 与来源路径见[小证据](evidence/p79-safe-rendezvous-source-2026-10-18.json)。本次以公共 `0dfaac30e0f5836f9b7e505f4724591773331fc4` 为基底，不改当前 R9、不可变 SDK04、Native DLL 或 Game，不增加 G2 信用。

实际 R9 AUTO658、667 分别完成七日驻守。日期 `53373672→53373840→53374008`，战争 `100663323` 战分保持 `-30`；己军 `167772577`、`486539625` 分别在 `2619`、`2623`，均 regular、路线为空。AUTO654 同帧兵力为 `1178+856=2034`；敌军在 `2629` 的两军为 `1246+219=1465`，另有 `1056` 人的 `654311862` 向 `2629` 移动。后两次七日快照显示这支增援从 `8756→2669→2609` 推进。AUTO662 敌军总数为 `2520`，AUTO671 为 `2509`，不是只有局部的约一千四百人。

因此这里确有联合兵力可能改变局部选择、而各军单独较弱的观察目的；合兵能否获胜仍未知。路线、抵达时间、地形、军团/指挥官、敌人后续命令与完整战斗模型不能由总人数替代。上述小回执也不能证明这两次驻守一定是战略错误。

原公共规划器已有同省闲置军队的 `_preoffensive_army_consolidation`、原 Native 合并验证及独立后验；分散时没有一般会合意图。既有 split 恢复对分散原军/分军明确返回 `native_war_merge_rendezvous_blocked`，普通新接触 forecast 则以选定单军构造 `attackers=(army_id,)`。本次不把两军压成一次未经证明的 1v1，也不扩张战斗许可。

新 `war_safe_rendezvous_v1` 已接入真实普通 `choose_one_life_turn` 返回链，位于原 siege/general/origin/H3937/Service/Native 守卫之前。它只复核一场主要防御战争的现有驻守选择，要求完整同帧兵力、全部可控己军闲置、其他高优先事务为空；另一场战争、已有军令、战斗、退却和原同省合并均保留原规划。

候选按以下现成接口逐步取得证据，不能一次把未查询的结果当成事实：

1. 只以当前己方闲军所在、且原生明确未被占领的真实防御目标为会合点，先查询移动军的 `preview-move-army-N-to-N`。
2. 对移动军和每支等待友军分别查询完整敌军范围的 `query-route-contact-horizon-v1-N`。所有回执必须匹配当前 snapshot/public/native/date/episode/connection，敌方时序也必须一致。
3. 保留整条已知路线几何审查；分别检查首个锁定移动段的起点暴露、每支等待友军在预计会合之前的已知敌军进入时序。另从完整 Native route/arrival 数组保守推断每段省份暴露窗口及反向边重叠，仅用于拒绝已知锁定段接触。一天无接触标记不证明整段安全；未知未来敌方改令和抵达结果仍明确保留。
4. 仅提出原 `move-army-N-to-N`。随后继续使用原路线逐日观察、原提交守卫与独立抵达后验；没有新 move/halt/attack 复合执行器。会合后重新取得同帧状态，让原同省合并逻辑、Native validator、原合并后验及完整战斗输入决定下一步。

R9 CAP2 实际广告了合并、预览、移动及 H1 能力，且当时同省军队有具体 merge typed step；这只证明该冻结 Native 的能力表与当时 action surface。它不证明现在分散部队已经可以合并。公共 `SubmitMergeArmies` 保留 living/controllable/命令布局检查，并在 `validate_merge` 成功后才 `submit_copy`；不新增一个假想只读 `CanMerge` API，也不把提交 ACK 当作源军队已移除。

锁定首跳终点也必须检查。当 SEM 与 Native 时序一致时，原 `_audit_war_route` 已会因敌军当前/目标/路径相交拒绝该路线；但原 `_fresh_route_contact_horizon` 不逐项比对敌军时序与 SEM 路线。新反例使用完整生产 H1 schema：起点 `2623` 安全、友军在 `2619` 等待，移动军先到 `2624` 需八日，敌军七日到 `2624`，两军首日均无接触。起点审查不能覆盖这个终点，新锁定段时序 veto 会在移动前拒绝；不依赖以后每日尝试取消一个已锁定的行军段。

另一个实际问题发生在 AUTO1118：同机 `2026-10-18T01:33:15.200896Z`、`native:11947/public970/date53377896`，战分 `-87`。独立 SEM1119 只有一支己军 `167772577`，正在 Native state6 退却，路线 `[2623,2622,8755]`，不是前面两军闲置的会合场景；三支敌军在 `2619` 围城。原 siege relief guard 在既有 global retreat 分支之前要求 sole army idle，因而返回 `single-idle-controllable-army-binding`。新的 `war_forced_retreat_observation_v1` 只识别已经发生的真实 Native 退却，将其交回原完整 global audit，再选择原 `life-advance-one-day`，逐日暂停重读；围城仍可见，没有新 retreat/move/halt/attack，不等同 P76 的主动撤退订单。缺 clock、状态/owner/路线矛盾、闲置或新窗口不取得这项资格。

必要资格为 18 个测试、37 个子例通过；加入两项新测试后的现 CI 战时分组为 76 个测试、62 个子例通过，`git diff --check` 通过。会合测试以真实658位置/654兵力作为可携带输入，明确把完整 ownership/occupation 与后续 preview/H1 标为软件夹具；通过真实 `Service.plan_turn`、公共 choose 的 core 返回接缝及后续原守卫，验证 `preview→移动军 H1→等待军 H1→typed move`。退却修复则将实际1119的完整 typed semantic 原样输入整个 Service 普通入口，不 patch core、不虚构 history，证明可以由原 global audit 选择精确一日观察。还验证锁定起点与首跳终点、等待军、旧帧/漏敌范围/已有军令/多战争，以及原 merge 提交和独立后验。不是新的实机安全路线、合并、攻击或胜利证据。

另通过冻结 Host04r03 的真实 `queue.load_cold_result_classifier()→owner.check_after`，消费上述 Service 实产的五类计划及明确参数化的旧 Native DTO，十个拒绝例通过。preview、两类 H1 与 move 使用原 `primitive_accepted` 调度分支，仅表明结果形状可继续消费，日期和业务信用均为零；该通用旧分支没有独立拒绝被改写的 planning actor，此局限保留在资格报告中，不能据此声称完整来源身份已获验收。退却的一日计划则通过原 clock validator，并拒绝外国 actor 和超出日期。没有修改不可变 Host04/SDK04；实际提交仍依赖原 SDK/Native 门禁及独立后验。报告来源、SHA 与各分支结果见小证据。

采用本改进需要后续新源码 generation；当前长局继续使用已经冻结的源。这不是本期三十年、视频完成或新1066开局的前置门槛。下一次自然业务验证应保存原 preview/H1、单次移动及独立 committed route、实际会合、合并源军移除、重新采集的 roster/model 和真实战斗后验，逐步记录获得的信用。

2026-10-18 补注：后续战斗输入链的 [Native26 独立构建与离线夹具证据](evidence/native26-build-and-offline-fixture-2026-10-18.json)已补齐；`machine_id: xenoamess-full-tower-eb9d2c1186`，生产 DLL 构建回执为 `01:45:59.763044Z`，隔离夹具执行为 `02:20:12.280774Z`。独立 Native 构建包 P79/P80 与本文会合候选分别记录来源：真实 V2 分发、原 archive 读取器和生产序列化的八个离线场景通过，三个有效场景均为 `available`、`input_observation_ready=true`、`monte_carlo_ready=false`。生产 Native26 DLL 尚未加载到 Game，`.4` 实机、普通 App/profile 接入及会合业务均未由此验收；本文此前状态、历史构建计数和会合实机信用保持原有范围。
