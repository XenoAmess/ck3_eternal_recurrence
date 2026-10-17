# 围城预测未准入时的普通单日守备续行

本次以公共 `81fe511570fa65589d887f4b8502b35d08184d4e` 为基线，把已离线验证的临时 P52 策略改为默认普通规划器代码，不依赖 owner monkeypatch。当前运行的 Game、录制、Native25、SDK48、SDK02 和外置 source freeze 均未被本源码包修改。实机摄入另记；本包不增加 M6/M7 能力分数。

`machine_id: xenoamess-full-tower-eb9d2c1186`；实际 UTC、输入路径与 SHA、源码 pins 和测试回执见[本次证据](evidence/p52-siege-research-public-2026-10-18.json)。仅解码已完成的24,314字节 AUTO1548；SEM1549只读前262,144字节，完整47,151,959字节正文未加载，189,608,765字节的1545未读取或复制。可移植测试夹具保存有界前缀的精确SHA和第一项不完整字段，明确不是完整实时快照。

## 触发问题与默认行为

AUTO1548 的普通规划器已经选择在8755驻守，war100663323、己军167772577、原七日绝对终点53358144；后置围城预测将它覆盖成无动作。敌两军在2619，路线为2622→2623→2619，第一点到达53358072。当前战分-12，己方1357、敌当前559/最大1038，只是观察值，不是胜率、胜局、解围或未来援军上界。原正式 combat-entry EU producer 不存在，Native25只有V2，双军研究预测没有接战资格。

`choose_one_life_turn` 保留原 ordinary baseline，先照常执行 siege ingress，再由独立 `siege_research_hold_continuation_v1.py` 消费它的查询/观察计划。只有原 baseline 本就是同 WarID、唯一己军、同省份的合法 stationary objective sentinel，且原计划仍是无攻击授权的 V2 研究查询/观察，才考虑恢复守备。一个或多个 defender 均可；已准入接战、具体移动、其他策略、V3 和未来正式 producer 的新查询不被替换。

必须同帧暂停、角色活着、地图就绪、无强制事件/交互，己军 regular、归当前角色、可控、无路线/移动目标、未战斗/退却。复用原 ingress 已验证新鲜的完整 hostile contact timeline，要求 H1 无冲突且首 arrival 严格晚于 H1末端。公开 native `ck3_12002_routes.cpp:837–851` 把 current Province 占用区间延伸到首arrival，因此这里一日原地占用是已观察路线一日占用的子集；不会把四日首hop当全程已证明安全。

终点只到 `date_raw+24`，位置、WarID、army、speed均沿用原普通决定，一天后再评估。下一天同类研究查询如仍不能授权接战，会在执行大V2之前剪掉；新路线与完整敌军 contact 的普通观测继续运行。保留旧研究拒绝、兵力、战分与 source frame；`overall_war_safe:null`、`siege_relief_achieved:false`。已经观察过的 query 与本次抑制的新 query 分开标注。

公共81fe没有 SDK48 的 `_guard_remote_ghost_day_v1` / `_guard_tactical_sentinel_native_armies_v1` 两个后置函数；本次没有删除或虚称保留不存在的公共代码。公共新 hold 独立要求 `ordinary_core_v1`、同snapshot/public revision、有效query sequence、唯一 player row、available状态和真实 Native CArmy身份；缺失、ghost、重复或过期时请求现有普通 army-strength 查询，不能制造fingerprint或继续sentinel。公共现有 general forecast、H3937、终战/窗口及 Native typed execution 校验均继续执行。

## 原版 profile 兼容只开放研究

`combat_profile_research_v1.py` 复用现有 lifecycle normalizer，严格接受 `.4` version/EXE/build-match、canonical `ordinary_campaign_succession`、`xar_enabled:null`、source及pact均为 `absent_by_verified_xar_mod_not_loaded`、合法 environment SHA。任意null、缺来源、错版本/EXE、错pact/环境不算原版资格；不把null改写成旧字符串 `xar_off`。

旧显式 `xar_off` canary合同保留原路径。新 verified-XAR-absent profile 能到达研究模型，但单敌也重标 `vanilla_profile_research_only/planner_usable:false`；多敌仍为 `multi_defender_research_only`。不能靠修profile将当前原版局转成自动攻击，原独立单defender动作门和正式EU门均未改变。

## 验证和边界

新6项 hold/模型门测试、独立profile compound、原18项雇佣/现金测试、11项war epoch测试、两个旧完整 ordinary hold/lease用例，共 **38项及17子例通过，5.47秒**。新完整链使用真实 Service.plan_turn→真实 ordinary core（只用wraps观测，未mock返回baseline）→原siege ingress→新hold→既有general/H3937→Service typed-prefix准入；只在原生读取材料边界回放已封路线/contact，不加载大输入。action_steps仅有既有 sentinel prefix，不含原七日或新一日literal。1548/1549夹具中的三条 CArmy/兵力缓存明确为合成测试侧车，敌军300/259拆分、最大编制/base power和Native身份不冒充实测；实际SEM前缀的空缓存保持在源夹具中。

另两项旧 canary用例在本包和内存加载的原81fe strategy上均以相同方式失败，尚未到本包新门；原函数AST也保持不变，未为本包修改旧夹具。首次直接pytest因未配置src路径为0项收集失败，后采用显式src入口；测试输出的 camera outside synthetic fixture 是旧合成相机拒绝，不是实机故障。精确细节均在证据中。CI沿用既有战争测试步加入两个新文件。

## R2 实际同日旧查询阻塞补证

初版P52仅覆盖 `inputs_query/inputs_observed`，遗漏冷SDK恢复后同日历史查询仍在、缓存不能跨代复用时的 `observation_blocked`。实际R2 AUTO22证明此缺口：native10214/public5/date53357976，当前strength16、route18、H1 20已经新鲜，原baseline仍是8755驻守，但旧1545输入查询的anti-repeat门先返回无动作。本包新增门只接受该确切reason和 `required_observation: fresh-v2-query-after-state-change`，其他观测失败/未知动作仍封闭；不删除旧历史，也不重做大查询。

新的[实际R2可移植夹具](../../ck3_autonomous_player/tests/fixtures/p53_actual_r2_antirepeat_projection.json)保存23,001字节AUTO22和33,504字节SEM23的source pins。SEM23同一完整帧有真实 `ordinary_core_v1/query1117`、己军NativeCArmy285212807及1357人数。新用例以这些真实材料和旧1548已封查询身份喂给完整 ordinary core与原始 siege ingress；只有历史相对index为合成控制值。它先确实走出与AUTO22相同的blocked reason，再由公共默认策略恢复一日hold，未mock原ingress返回值。当前冻结v2不热改；Root通过已有MCP的一次人工修复日是否实际完成另记，不能算自动 ordinary 成绩。

单日守备是恢复连续观察的受限策略，不是完成主动救援。下一步须保留 ordered joint roster及每军 regiment/knight/commander、反制和战宽计算，先做有预算的原V2减缩输入研究；缺失的phase事件、后续滚动修正、伤亡/俘获尾险与正式效用仍列为缺口。通过现有MCP作安全首hop时，每日重新绑定所有敌军、路线和停点；4日ETA不能用一次H1跨过。任何有预算接战试验都要保留单次pending、不重放未知结果，独立采集实际CombatID、战斗角色/军团、日损失、退却、战分及头衔后验来校准。双敌不能压成1v1，也不能仅凭兵数放行；本源码包没有开启该试验。
