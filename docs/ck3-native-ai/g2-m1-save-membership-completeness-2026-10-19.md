# M1：SAVE领地与宗族成员完整性

[`campaign_score_save_reader.py`](../../ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py)现在把缺失/循环领主链保留为unknown，已经接入现有`project_metrics`，供低频正常checkpoint投影调用。它不会因为某县没能走完归属链，就把该县排除并报告精确失地；未闭合的成员集合也不能产生精确Q、控制均值或宗族境外折价。

机器`xenoamess-full-tower-eb9d2c1186`由本次`tools/ck3_live_run_id.py machine`读回，观察时间`2026-10-19T04:49:53.918271+00:00`。工作开始HEAD为`d74afbf395301c8546d861d6130902b425deab32`，闭场时Root已推进至`dde6cc5f7dccb88ba48f34b5f0f6592e17cb3dd5`；本叶未stage/commit。源码、消费者与测试pins见[小回执](evidence/g2-m1-save-membership-completeness-2026-10-19.json)。本轮只用内存中的小合成SAVE文本，没有读取T0或其他实际SAVE、mutable Driver、现场或RPC；没有改runtime/cadence/Native。先前monthly collector四件保持冻结。

## 新的最小合同

纯函数`audit_saved_county_membership_v1`直接使用现有`SaveProjection`内已保留的title/holder/de_facto_liege、character→house、house→dynasty/parent_house及显式`county_baronies`；不增加导出、缓存或身份builder。结果进入`detail.county_membership_audit`：

| 字段 | 含义 |
| --- | --- |
| `source_ref/date/actor_id/founding_house_id/founding_dynasty_id` | 现有SAVE来源、保存日期和固定评分范围；没有新造运行身份 |
| `title_census_complete` | stream已正常complete、未知decoder key为0且存在landed_titles容器；缺容器不能冒充空世界 |
| `states[title_id].geographic` | 当前显式地图映射证明为地理县时true；未映射/冲突/身份不唯一时null |
| `states[title_id].in_player_realm` | true / false / null；另带reason及终止title ID |
| `states[title_id].family_factor` | 原评分口径的0、1、0.5或null；缺/冲突/循环家族链不补0或半价 |
| `realm/dynasty.complete` | 该范围的县成员集合已闭合；不能用global geography标志替代各自scope |
| `known_member_title_ids/unknown_title_ids/count_lower/count_upper` | 已确认成员、仍待核成员及县数范围；census/创始范围缺失时upper为null |

直接holder=actor足以证明该title链属于玩家，无需等待更高上级。外县沿完整title链到一个明确foreign holder的完整无上级记录，仍可确认境外；沿用SAVE可选`de_facto_liege`在完整记录中省略表示无上级的合同。引用的上级title不存在、循环、holder缺失/冲突、liege scalar冲突或无效时均为unknown。这里区分的是完整foreign root与无法解析的引用，不把缺失节点当作独立根。

地理资格只接受非空、有效且不冲突的当前county→barony→positive province映射，并要求该county key对应唯一saved title。无效/空映射、跨县复用同一barony/province、重复county key和缺key均不能证明地理资格。未映射`c_`既不自动计为土地，也不自动当动态无地家族排除；若它仍可能属于该realm/dynasty，该范围保unknown。若它已明确境外且不同宗族，则不必使玩家范围失去完整性。

house/parent-house缺节点、循环、重复scalar、缺dynasty或父子dynasty矛盾时，相关family factor为null。完整character记录确实没有house、或完整house明确属于其他dynasty，仍是已知排除；实际同dynasty独立house根仍使用原0.5口径。固定本场T0锚继续由caller显式传入，不借用旧局174。

## 现有评分消费者的边界

`project_metrics`保留原返回`(metrics, detail, facts)`。成员完整时原县数/Q/K保持原值；不完整时：

- realm县数可保留安全上下界，`detail.realm_county_count=null`，另列`known_realm_county_count`。Q和control_average保持unknown，不能对已知子集求均值当全体。
- dynasty县数继续沿用原unknown兼容合同；上/下界只在audit保留。K在family成员或其realm内外折价未知时保持unknown。
- `detail.realm_counties/dynasty_counties`仍列已确认成员，必须结合audit完整性读取，不能再以list长度冒充全量。每个realm derived row带`realm_membership_complete`；旧CLI把这些row用于T0 cap时，projector会拒绝不完整子集形成cap。没有改CLI所有权叶。
- facts在不完整时明确“已确认N县；成员关系未闭合，不能据此计算失地”。targeted occupation enrichment只有现有Q为bounded/observed才可提升；新不完整成员Q为unknown，已用回归证明不会被空/局部省份集合重新提升。

由此可以直接作为正常低频checkpoint producer的canonical mapper：每份已保护immutable SAVE只按现有一次stdout stream构造projection，再调用原`project_metrics`。上游继续负责实际机器、SAVE SHA/锁定身份、decoder/static来源和固定创始锚。只有前后scope可比较、保存日期有序且**双方该scope complete**时，才能把两个`known_member_title_ids`集合的差集发布为确定失地；否则只能输出已知成员与unknown/范围，不能补成精确缩水。

本轮没有新增定时worker、触发SAVE或实际loss差集结论；年度/继承/己方战争结束等低频调度仍由[月度生产接缝方案](g2-m1-monthly-met-production-2026-10-19.md)的runtime/storage owner接入。本场T0历史summary没有本合同的审计位，不能倒填为已通过；未来若需要完整前后差集，应消费仍受保护的原T0并实际记录新的单次投影，而不是挪用旧县集。自动游玩不等待这项离线工作。

## 验证与留存

新增[`test_campaign_score_save_membership_v1.py`](../../ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py)11项内存小世界用例，覆盖完整realm、真实境外、缺liege节点、循环、holder/liege冲突、地理映射缺失/冲突、动态未映射county、缺key/重复key、house祖先缺失/环/冲突、父dynasty缓存边界、lowborn和其他dynasty、未知decoder/census，以及不完整T0 cap和targeted enrichment防误提升。

另选现有3个直接受影响用例：CLI主流程一次stream/source、重复scalar、历史重复house与固定T0锚。第一次有效运行14项中13项通过；旧house用例指出dynasty县数原unknown被升为bounded的兼容差异，已恢复原unknown合同。随后只补跑该旧用例及两个受影响新用例，3项通过（内部0.004秒/外层0.1498185秒）。其余已过用例未重复。更早一次从unit目录运行仅因PYTHONPATH未设置而import失败，0业务测试执行；回执保留该事实，未当作代码失败或通过。没有跑旧泛矩阵或任何Native业务资格。

通用存储策略1.0.0；本包为一个已有小source修改及三个新增小件，计Root原other研究共享128MiB，不新设预留。观察时Z盘total4,096,787,476,480 B/free178,402,668,544 B只是当时读回，不能当预留。机器记录180日复核；producer闭场，后续大输出0。M1历史complete、G2仍6/8，没有业务信用增加；Root统一提交。
