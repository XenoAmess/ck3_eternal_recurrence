# 罗贝尔首局三十年复盘与下一局的实际采用

**首局的运营结果很差，保地优先级和研究到运行的交付都没有做好。** 终点玩家实际统治县从10减到2（−80%），领地品质量Q从15.975减到2.7435925；宗族县从8减到7、宗族土地品质量K从12.675减到7.3875。现金239→251.85072和两级宗族传承不能抵消这些损失。不能用治理分81.8或“成功运行三十年”评价为运营成功。

本次是既有小证据及公共源码复盘：`machine_id: xenoamess-full-tower-eb9d2c1186`，身份由本次 `tools/ck3_live_run_id.py machine` 实际读回（工具chunk `75c953`）；2026-10-19T01:47:25Z已取得当前UTC，以下施工在其后进行。当前游戏、安装、Steam、现场、部署与大SAVE/Driver/视频正文均未读取或操作。首局事实来自[10月19日交接](../handover/2026-10-19-robert-first30-scoring-vacation-handoff.md)、[交付JSON](evidence/first30-scored-film-delivery-2026-10-19.json)、既有 `score-result-03-presentation.json` 与 `final-scoring-validation-07-player-wars.json`；两份评分小投影位于交接所指 `P/scoring-draft01/`，均带上述历史机器身份。本次同机读到历史材料不构成当前实机验收。旧P43原审计机器仍为 `machine_id: unknown`，不追认。

## 确认的错误和因果边界

| 错误 | 证据支持的结论 | 不能推出的结论 |
| --- | --- | --- |
| 处理重大让地事件时，没有把已经审过的来源知识可靠带入实际namespace，拒绝策略还绑定旧calculated ID | [P43](p43-populist-current-source-and-natural-audit-2026-10-17.md)的AUTO193：`faction_demand.1001 / instance41 / calculated3571001`被判unknown，执行首显示项native2/API3；原版该项授民粹独立，实例实际advanced。旧known hook固定3551001，离线重放证明即使学成known仍会漏掉本局ID。 | 当场unknown首项续行本身符合用户规则；问题在此前知识携带、ID绑定及专用语义没有完成，不能靠暂停陌生事件或改写旧选择解决。 |
| 低估让步的领土范围，缺失完整损失归因 | [P50](p50-populist-loss-prevention-2026-10-18.md)核原版：授独立可扩展到派系县所在法理公国内仍属目标realm的县，非只移交窗口target。选择后来源native4191的直接持有集合从5个混合层级ID变3个，2196、2200移出；当日战争数2→0。 | 5→3不是realm面积少40%；2196=c_messina仍是来源顺序推导。没有新holder及各场终战独立结果，不能说10→2的全部损失由AUTO193造成，不能说两场战争都由它结束。 |
| 没有把“代码已修”和“本场已采用”分开管理 | P43动态绑定在后来的SDK48可核；P50跨load、P83战时资金门、P87政治生存/绝境及resident继承随后都有公共实现和软件验证；交接明确冻结Host06未采用后继继承源，其他后继修复的本局采用未证。 | master里存在某模块、测试通过或CI通过，不证明冻结Host实际导入该模块，更不能追认它在首局拦下某次建设、买到佣兵或保存了领土。 |
| 运营观测不足，容易把旧缓存和局部成绩当现状 | P43至P49的继承held缓存长期绑定native4191，不能表示当时native8533等新帧当前领地；P50R1重新查询native8535才有fresh集合。终点可确认当前player realm仅2县。 | 直辖domain、混合层级held集合、宗族县数、整个realm县数是不同范围；首战赢下2200不表示终点仍持有，WarID消失不表示获胜。 |
| 把续行完成放在可核运营反馈之前 | 首局缺360月同口径采样，SAVE晚于三十周年8日；E财政/M军力/H合法继承共50%权重尚未知，只有L/U/D贡献28.50→18.2657已确认。 | 不从现金余额推净财政，不用已集结人数代替军质，不用旧SEM169后继预期证明终点合法继承；不能将未知项取中值后称完整总分。 |

终点当前战争184549379是玩家反抗领主要求的战争：玩家是叛乱进攻方。它不应计入玩家自己领国内战占比，但也不能因此当成低风险对外战争。[P87](p87-political-survival-crisis-profile-2026-10-18.md)已核败战可带来条件监禁及剥夺头衔等处罚理由；这不是自动剥夺所有头衔。当前小证据不足以把其实际处罚写成首局失地原因。

外交上，本复盘没有找到已闭合的“某次婚姻/联盟拒绝直接造成八县丢失”链，不能编造。新研究另发现宗主主导战争在现有采购focus中的范围缺口；宗主战争可能波及玩家，但target命中也不是确定失地，交由M5来源审计保持独立。[M0来源研究](g2-m0-research-2026-10-19.md)及[小证据](evidence/g2-m0-refused-demand-white-peace-source-2026-10-19.json)已核此反抗领主CB的白和也有剥夺/监禁处罚理由，白和不能自动记作政治风险清零；新来源结论不追认为首局实际发生。

## 写入智能体的经验

以下经验已保存为可读的[版本化经验目录](../../tools/g2_saved_campaign/robert_first30_lessons_v1.json)，与[部署复验入口](../../tools/g2_saved_campaign/qualify_robert_first30_lessons.py)绑定。采用现有已验证policy，而非另加一套与普通规划器分叉的手工策略。

1. **保地事件的知识要随来源走，不能随旧实例ID走。** 只迁移已分析registry条目、引用facts和经验证的原版源，不迁旧玩法ledger。实际新loader必须能将当前已审民粹letter与新calculated ID绑定；仍然不认识的事件继续原生采集、首显示项、批后离线补齐。已知民粹窗口优先保地拒绝并承担派系战，选择回执不授胜利信用。
2. **战争现金先于可推迟的建设。** 采用P83共用门，完整付款后保留当前军费、已有未付承诺及合格应急合同报价；缺输入只延期可选工程，继续合法战争。P80累计包预算、P87恶化/政治生存与条件兵数反转共同约束采购，不能因为当前推进就当建设窗口。取消退款及借款未到账始终记零，未闭能力如实诊断。
3. **自然继承属于同一个长期目标，未知动作不能靠重启重发。** 带上常驻App/Queue durable ledger、真实pre/post、完整title/goal绑定、dispatch前消费的一次许可和异常finally撤销；后继家庭机会只用当前合法继承人及新关系观测，旧未决提案归历史且不冒充成功。
4. **保地、财政、军力、继承分别用来源明确的当前观测追踪。** 固定开局宗族/家族和分母，角色转换不重置成绩；复用普通AUTO已有返回体采月度与准点终点，不新增每回合RPC、不重扫大SAVE/Driver。任何战争或让地的后验必须区分ACK、原窗口消失、新战争、付款、部队可用、持有人及终战。

这四条不是新增“无输入就停止整场”的运行门槛。当前公共代码没有已闭合的退款/贷款资金链、完整防守退出效用或所有宗主战争采购策略；本次不会用一份经验JSON把它们写成已实现。

## v20261019必须真实携带什么

| 项目 | 新局一次性采用/核验 | 首局已有信用 |
| --- | --- | --- |
| 民粹来源及跨ID知识 | 实际新state迁registry/facts，来源绝对路径重绑定，选定新SDK执行 `qualify_populist_source.py --verify-cold-id-rebind` | P43/P50有软件重放；后继SDK48 exact知识有读回，不授未来拒绝或保地信用。 |
| 战时资金及危机 | 合批带P80/P83/P87 helper与strategy/service消费者，freeze实际叶与已审源逐项比对 | 公共软件资格已存在；冻结Host对各次历史动作采用未证。 |
| resident继承 | App/Queue/Native tuple、ledger、Source epoch及family handoff完整闭包；同resident执行普通AUTO | 首局真实两次转换不等于后继resident修复已部署；G2 M7仍缺更广seed/government及精确SAVE lineage。 |
| 观测及性能 | 开局固定anchors、月度小采样、准点终点；记录秒/游戏日、零日轮占比、步骤p50/p95、回包和Driver增长 | 旧场仅稀疏样本；不能用少打仗、投降更早或不处理事件换吞吐。 |

新工具用法（路径由新局实际冻结与state回执提供）：

```text
python -B -X utf8 tools/g2_saved_campaign/qualify_robert_first30_lessons.py --package-root NEW_FROZEN_SRC --reference-root REVIEWED_FIXED_SRC --state-dir NEW_STATE --output NEW_RECEIPT.json
```

它先核必要源叶的实际raw SHA及UTF-8换行规范化SHA；旧冻结源或缺叶失败时不运行知识资格。随后沿既有生产loader/known policy对已发生P43投影做cold-ID来源复验，保留独立小回执。代码不连接游戏、MCP或OBS，不新增周期查询。PASS只证明选定源码与携带知识，不证明实际Host/App/Queue导入、Native兼容、佣兵/保地或胜利；这些仍按已有真实启动/业务回执确认。`REVIEWED_FIXED_SRC`须为本次已审的固定来源，不能为了PASS把旧冻结树自己当参考。

本工具新增5项定向部署回归：陈旧冻结源、缺叶、仅换行差异的双SHA保留、父目录越界及过大单叶拒读；2026-10-19实际执行 `python -B -X utf8 tools/g2_saved_campaign/test_qualify_robert_first30_lessons.py`，**5 tests / 0.046s / exit0**，工具chunk `a5191c`。这不是新局实际采用回执，尚未对未来state运行工具，也未重跑既有policy测试。

用户本轮已要求复盘后从1066开新罗贝尔三十年，版本为v20261019，覆盖旧文档“暂不开下一局”。新局仍须当前机器实际EXE/build、Steam新鲜离线画面、账号/现场owner、容量及完整普通规划器；不恢复旧场或回滚抹去首局历史。片名不进入实时HUD，旧蓝色面板不得进入新录制。未来评分片压至15秒由独立工作包落实，旧成片不改。

本包仅仓库小型源码/经验/记录，单文件上限16MiB，新增量远低于1MiB，0重型输出/删除/新重型预留。按统一存储策略1.0.0，Git源码/记录不进入本机逐文件删除器；小证据180日复核归纳，派生测试临时目录已由原测试清理，不刷新旧SAVE/素材期限或容量资格。协调者统一核当前容量及commit/push，本worker未暂存、提交或推送。
