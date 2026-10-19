# M1：普通月度帧的评分来源映射

**当前无需新增RPC、可直接进入月度数值评分的最小输入仍是现金`gold`。** 当前SEM/paired-MET足以保存准确月界、当前actor、钱包和玩家战争小投影；它们还不足以闭合L/E/M/U/D/H。已有cash-v2确有可用的收入/费用原生读器，但其普通调用结果没有自动进入月度MET，不能把AUTO动作前的财务包当动作后的月点。不能通过纯字段改名填平这个来源缺口。

本审计固定公共源`dc4b7d56`，先读[月度cadence](campaign-score-monthly-cadence-v1.md)、[评分合同](campaign-development-scoring-v1-design-2026-10-19.md)及[离线适配边界](campaign-scoring-offline-implementation-2026-10-19.md)，再读runtime owner提供的三个小源码producer。`machine_id: xenoamess-full-tower-eb9d2c1186`由本次`tools/ck3_live_run_id.py machine`实际读回；观察时间`2026-10-19T02:39:32.076684+00:00`，来源pins见[小映射JSON](evidence/g2-m1-monthly-observation-source-map-2026-10-19.json)。这是源码审计，没有读取月度实产文件或证明某个样本已经产生。M1历史`complete`、G2总进度6/8均保持。

## 当前生产链与真实范围

`root_p37_mcp_entry.py::root_current_runtime_metrics`只取**一次**`take_internal_semantic_snapshot()`，在这同一snapshot调用`candidate()`。MET返回原snapshot/public/native revision、date、actor、episode和connection generation，同时附月度candidate；并不额外查询campaign-root、cash、全世界领土或军团。

`root_score_month_samples.py::establish_anchor`以真实T0 paused/map-ready founding frame固定campaign/founder，house/dynasty目前显式null；不复制旧局174。`ordinary_sample_candidate`只在准确月界输出，`raw_metrics`中只把合法`played_character_gold.raw/100000`升为observed。`root_p37_sdk_queue.py`以初始SEM采baseline，普通AUTO后取paired-MET，再给候选绑定实际response路径/SHA、AUTO引用及Game PID/creation，create-only写出并fsync后更新cursor。同槽后继零日帧不会再算一个月；没有月点就不能用后来的帧倒填。

CAP是能力、episode、driver恢复与控制合同来源，**不是资产数值快照**；字段显示query supported不能替代某次query的数值输出。原生semantic publication由`native_driver.py::_semantic_snapshot_from_frame`归一化；普通的`played_character`只保留身份/生死、可选压力、特质成员、主继承人及婚姻关系，不包含house/dynasty或县域账。

## 字段、单位与可否计分

| 已有来源与字段 | 单位/所属scope | 同帧要求 | 当前月度处理 |
| --- | --- | --- | --- |
| SEM `played_character_gold.{raw,scale}` | Q100000金；当前played-character个人钱包，允许负数 | 同一次paused snapshot的date/actor/public/native revision；由paired-MET回执补Game与generation出处 | **gold observed**；不能由钱包反推债务为0 |
| SEM `active_wars`，MET `war_count` | 玩家当前战争记录/条数；不是全世界战争 | 原snapshot；保WarID、player_side、对手、相对分数 | 仅诊断；仅战争数和attacker/defender不足以构造评分`rebel_share`或证明本国县域叛乱比例 |
| campaign-root `player_domain_size/limit` | 原生domain占用/上限整数；不是县域面积 | root明确的date/native revision/player以及外层snapshot绑定 | SEM/MET未默认发布；即使已有同帧值，也只作domain诊断，不填`realm_county_count`/`Q_realm` |
| campaign-root `held_title_partition` | 个人直接持有的county及以上title；含高层title和合法无Province家族county | 只能用fresh root；SEM继承缓存保留其原source date，不能重新盖当前帧 | 可按[M1新口径](g2-m1-research-2026-10-19.md)识别direct地理county；不是全部realm，不能填L/D |
| campaign-root直属封臣、相邻holder；faction `county_exposures/surrender_impact` | 关系目录、风险相关县子集 | 各query的明确scope和同帧绑定 | 不构成所有层级附庸的完整county闭包，也不构成宗族境外资产目录 |
| marriage projection `rows[].played_house_id/played_dynasty_id` | 当前actor家族/宗族ID；不等于孩子preview或当前heir的谱系 | 原生query对五候选校一致；返回值只有native revision/actor，月度复用另需原调用context与回执绑定 | 可作为未来**T0尚未推进时**已有普通FAMILY query的创始锚输入；当前baseline helper未消费，不能用后期ID回填旧T0 |
| cash-v2 `player_monthly_gross_income` | Q100000金/月；played-character personal gold收入 | exact .3/.4 `native-income-minus-total-expenses-v2`标记、同actor/date/native/public/snapshot；ready true | 已有读器；当前MET没有此包，保unknown |
| cash-v2 `player_monthly_total_expenses`、`player_monthly_net_income` | Q100000金/月；total已含军费；net严格gross−total | 同上；拒绝缺v2 marker的旧错标net；不把一次性钱包变化乘12 | 可与同包gross组合；当前MET缺来源，保unknown |
| cash-v2 `military_expenses.current/all_raised.gold_raw` | Q100000金/月；`actor_owned_military_once_across_all_wars`，十槽resource vector的gold[0] | owner/resource_id/war_ids、raw_scale/time_basis/source_scope及ready均一致 | 真实当前与全动员报价，不逐WarID重复求和；不是未来战争费用上界；当前MET缺来源，保unknown |
| construction `existing_commitment_gold_raw`/reserve | 调用者政策/预算参数 | 不能替代逐合同的到期付款/本金全集 | 不据传入0把`due_commitments`判为0；借款和退款未到账也不计钱包 |
| SEM可选`army_strengths[].current_soldiers/maximum_soldiers` | 当前公开CUnit内人数/编制整数；scope_role可为player、active_war_ally或enemy | driver cache核snapshot/public/native/date/generation/episode/actor及当前scope；读器无结果时不把空数组认作0兵 | 可保留带scope的诊断；不是未集结常规兵完整名册，maximum不是现兵，不能填`P_quality` |
| SEM可选`army_strengths[].ai_base_power_raw/scale` | Q100000原生AI力量缓存；不是标准兵当量 | 同上 | 不能改名为评分P，不能据其比值声称胜率 |

L仍需完整player-subrealm县集合及每县发展、控制、已完工地产、敌对军事占领比例；D还需固定D0/H0及分支关系、县实际holder的家族/宗族、境外/境内去重权重、完整传承等级。当前普通帧没有这两个资产集合，`realm_county_count`、`dynasty_county_count`、`Q_realm`、`K_dynasty`、`legacy_ranks`不能互相替代。

M除同包费用外，还缺全部可调遣、含未集结的常规levy/permanent-MAA去重名册、实际当前人数、与对手/地形/战斗阶段无关的有效damage/toughness和冻结征召兵参照。Army观察混有同盟、敌方、临时/雇佣军风险，不能靠只挑scope_role=player解决兵种完整性。H的primary-title heir不等于合法player-heir或全部合法backup；本包不改变H。

## 最小可落地接缝与必须先补的source

1. **当前直接保留既有最小投影**：gold、原frame及玩家战争诊断；未知指标继续有单位与原因。无需再写一个重复cash-only mapper或重跑已过cadence用例。
2. 可新增纯cash-v2 adapter，但只有普通规划**已经取得**同一月点的cash包时才启用：输入sample snapshot、原cash-v2 packet、实际source response pin及其调用context；复用`normalize_war_cash_current_resources_v1`，核完整source后映射gross/expenses/current/all-raised。缺包或任何frame差异返回unknown，不补查询，不以AUTO前包覆盖after-MET。完整E仍等due ledger，不因有四个流量就授确定E。
3. 该adapter当前还缺生产接缝：SEM/MET未携带cash包；现cash公开wrapper只补`queried_snapshot_id/revision/native_revision`，不单独保Game PID/creation/generation。需在原普通query调用处保留这些context，再随已取得的包进入同源候选。`construction_monthly_budget.source_cash_resources`及`pre_cash_v2`可以是来源，但必须核其真正query frame，不能因它属于相邻AUTO就放行。这里是未来最小source更改位置，本包**没有修改冻结SDK、COW或现场**。
4. 对领地与宗族，先实现/验清完整且声明范围的原生县成员读取与品质字段，再把已取得的同帧小切片交纯评分投影；对军力先补常规regiment完整性和有效属性。单纯扩展月候选JSON不能产生这些原生事实。T0锚若仍无已获普通FAMILY来源便保unknown，不强造月度D基线。

本包只新增本映射及JSON，不改生产源码，没有值得运行的新业务测试；只做JSON解析与diff格式检查，不重复旧M1/cadence矩阵。0现场/RPC、0编译、0SAVE/活Driver/媒体正文读取、0重型写入或删除；小件低于32KiB，计Root剩余128MiB共享研究额。存储策略1.0.0，当前Z容量只读为total4,096,787,476,480 B/free178,416,340,992 B，非原子预留或新局容量准入；小记录180日复核。
