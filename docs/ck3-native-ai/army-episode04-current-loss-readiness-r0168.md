# R0168：William 暂停帧损耗输入与兵团组成实读

2026-10-05。本记录更新[实际损耗写回专题](army-attrition-soldier-writeback-12003.md)中“当前输入是否已在本期 William 源发布”的证据切点。Root 的 R0168 原始 Jan11 冷载已实际读到 `loss_application_inputs_v1`、全部 actual 兵团的 composition、完整 DATA records 与 supply clock。**闭合的是当前输入 primitive 可读性；围城预算56不是已经扣兵56，真实饥饿阈值跨越与实际整数扣兵仍待证。** 本文仅沉淀既有原生研究及已采集暂停 artifact，没有新采样或策略施工。

## 实际身份与暂停窗口

运行输入为 exact CK3 1.20.0.3 / stock EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`，冻结 `C:/w/e4a02` 提交 `ffc29e7c6f616592c0186f18570759eb36f30206`、a07 native build，与[同场当前完整月净额](war-cash-net-live-r0168-2026-10-05.md)来源一致。实际查询 `source.game_version` 和 `source.executable_sha256` 仍为 **null**，上述外部冻结身份不能回填成 payload 已读字段。

Root 的 `r0168-paused-initial-a02`、`r0168-loss-strengths-a01`、`r0168-net-loss-after-a01` 均为 William **33388**、episode `native-33388-8baabd4dc94f`、snapshot **native:2**、public revision **3**、native revision **2**、date_raw **53147160**。独立 snapshot 前后 alive/map_ready/paused=true，active_event=null，玩家军队的 FullID、owner、province、目标、完整 route、combat/retreat/state 相等。**新增游戏日0**；query accepted=true、status/scope_status=partial，其中两个 available 行可用，ghost166 的显式缺失保留。

首次 initial 的 `army_strengths=[]`。after 保存的是 service 缓存的 query 行，所选三行逐字段与 strength query 完全相等；它是独立的状态快照后读，**不是第二次独立人数查询**。本帧可作后续独立人数基线，不能制造两个端点整数 loss 或期间无补员的证明。当前 snapshot 军队行未发布 commander，尚未绑定本次 commander 身份。

实际请求只有既有工具与参数：

```json
{
  "tool": "ck3_query_army_strengths",
  "arguments": {"army_ids": [0, 16777220, 166], "expected_revision": null}
}
```

`army_ids` 为当前 public CUnit FullID；`expected_revision:null` 使用 fresh paused service snapshot。没有另造 `include_loss` 参数。native_carmy_id 由响应实际解析，不能用旧 session 或 public ID 猜代。

## 当前实读值

以下 budget 单位为整数士兵（scale1）；fraction / stock / monthly change 均保留自己的 raw 与 scale100000。

| 当前量 | Main0 / native0 | Sea16777220 / native16777220 | ghost166 |
| --- | --- | --- | --- |
| actual 兵数 / 上限 / 团数 | 5660 / 5660 / 13 | 1086 / 1087 / 14 | native_carmy_not_found |
| stock | 8299737 / 100000 | 29122808 / 100000 | unavailable |
| monthly stock change | -1000000 / 100000 | 0 / 100000 | unavailable |
| current attrition fraction | 1000 / 100000（1%） | 0 / 100000 | unavailable |
| siege_active / siege_loss_budget | true / 56 | false / 0 | 字段缺失 |
| raid_active / raid_loss_budget | false / 0 | false / 0 | 字段缺失 |
| current_supply_loss_budget | 0 | 0 | 字段缺失，不能补0 |
| whole / definition≤0 / supply eligible / intersection | 5660 / 5600 / 5660 / 5600 | 1086 / 1077 / 1086 / 1077 | 字段缺失 |
| type available / absent 团数 | 8 / 5 | 2 / 12 | 字段缺失 |
| siege tier>0 当前兵数 | 60 | 9 | 字段缺失 |
| 完整 DATA blocks / records | 13 / 13 | 14 / 24 | 字段缺失 |
| DATA native_can_replenish=true / chunk=true / prepared非零条数 | 0 / 0 / 0 | 22 / 0 / 0 | 字段缺失 |
| actual bucket / selected phase / 下次条件桶机会 | 0 / 5 / +25 admitted days | 20 / 5 / +15 admitted days | 字段缺失 |

Main0 当前在1506、sieging3、route[]；Sea 当前在725、embarked4、目标1506、route[1506]。ghost166 在玩家 snapshot 中仍有 public 行，但 native resolution 为 `reference_absent`、raw_reference=-1；actual strength、composition、loss inputs 缺失。它不能当0兵军队或0损耗正例。

Main 的 actual团 FullID 为0–12。3、6、9均 onager/tier1/current20；2、8为 conrois/tier0/current100，5 bowmen/tier0/current400，11 light_footmen/tier0/current400，12 pikemen_unit/tier0/current400。其余5团类型 absent，tier=null、observable=false。**类型 absent 不等于观测到定义 tier0。** 60个 tier>0 兵数与 aggregate definition≤0=5600 一致，无法据此扩写所有 loss 分支都排除攻城器。

Sea 的 actual团为50–62、82，共14团；52 armored_footmen/tier0/current200，53 mangonel/tier2/current9/max10，其余12团类型 absent。全部27团 FullID 唯一、人数之和/上限之和与各自军队聚合相符，原生顺序和完整记录均保存在外置回执。

Sea56–60的完整 DATA record_count=0 是合法结果，各团仍有1个 actual士兵。其余完整 DATA 总计24条，22条 persistent `native_can_replenish=true`，全部 `native_chunk_can_replenish=false`、prepared fraction0；两项 native bool 是不同 predicates，不能合并成“海军没有补员能力”。Main13条两项 bool 全false、prepared0，只证明当前暂停点，损兵后或日历月首补员输入可能变化。

## 预算与实际扣兵的边界

`siege_loss_budget=56` 在本帧数值上等于 floor(5660×1%)，来源为 whole-strength budget getter，不是已执行事件计数器。现有原生执行树已闭合预算、实际兵团与 record/chunk 写回；实际 allocator 按 native 顺序分配整数余数，不能用“每团独立乘1%取整”代替。当前聚合四个 strength getter 也不是逐团 supply-eligibility 列表。

Main stock82.99737/month−10、current supply budget0，远离严格 `<10` 饥饿条件。周期执行先更新 stock，再取得损耗预算、再写人数；此前预算0或事后按新人数算出的预算，不等于那次实际执行预算。Sea stock291.22808按当前原始读数保存，不以当前容量另作静态重截断。

原生语义复用 [当前补给与损耗](army-current-supply-capacity-attrition-12003.md)、[双时钟](army-monthly-update-order-12003.md)与[实际人数写回](army-attrition-soldier-writeback-12003.md)：siege 为 `24E8560` predicate + rate `5C69618`；raid 为 `Army+1E8` association + rate `5C69098`。四个 strength flags0/1/2/3 分别 whole / definition≤0 / supply eligible / intersection。旧反向命名已追加勘误，历史 packet 不重写。

[R0162 周期与县界正例](army-episode04-periodic-and-county-arrival-loss-r0162.md)保持其原身份窗口：child围城3120→3089净−31，当窗 supply82.99737→74.22545并非饥饿；main县界arrival2540→2413净−127、+188未变，分配余数独立解释。本次不要求重做这两个已核正例，也不能借 Robert/R39 或 R0162 代替 William R0168 的真实饥饿正例。

## 后续最小观察与仍缺字段

现有 strength query 足以再次读取 stock/current budget、clock、完整 actual人数/composition 和全 DATA。推进前后仍需同 ArmyFullID/nativeCArmy/owner/commander：commander 用既有 `ck3_query_army_commander_candidates_v1` 独立绑定，siege context 可用 `ck3_query_war_occupation_targets_v1`。实际日期/桶/anchor必须按新帧重读；本帧Main+25/Sea+15仅为下一条件桶机会，不承诺成功更新。

沿用 Root safe sampler 的零dwell resume/pause和 paused health，真实 raw/day span原样记录；30实际日、40pulse或10wall分钟为有限窗口，先到者停。出现事件、战斗、月历补员边界、编成/集结/分合军、Army/owner/commander变化或province/route/embarked→land变化时保留窗口并停止或降因果强度。行进Sea的到岸/县界不能与纯周期损耗混为同一原因。本文没有发起这些操作。

当前明确缺口为：

- **真实饥饿 threshold crossing + 非零整数实际 supply loss**，不是当前供给 getter可读性。Main远离阈值，不盲等8次成功更新，不追认历史缺字段 source。
- **县界输入 DTO**：当前 bridge 未发布 `24E6670` county-entry budget/modified minimum/proportion/完整进入条件；province/route/人数端点可作 arrival 关联，不能代 applied ledger。
- **逐团 native supply eligibility 与特殊写回条件**：没有每个 actual团 `2A956D0` predicate、fallback/character例外的独立DTO；现四个聚合输入不补造缺失列表。
- **loss/refill/death区间流水**：端点 can predicates/prepared与FullID完整对账可减少混杂，不能排除未观测的损失/补员抵消；不由净兵员变化推出死亡统计。

当前 primitive 可读性实机成立；production-live applied-loss/starvation loop、影片镜头时码/clean span、1×完整审阅、影片与交付没有因此增加完成信用。

## 小型 evidence 与源码 pins

根目录 `CROOT=C:/ck3-war-episode04-research-20261004-a01`；以下是本机证据定位文字，仓库链接均使用相对路径。原文件永久保留。

| 已核文件（CROOT相对） | 字节 | SHA-256 |
| --- | ---: | --- |
| `native-live-merge-r0168-originaljan11-a01/responses/r0168-paused-initial-a02.json` | 168966 | `b7057838d34d8c31d79d165d207ecf010e5c4bd23300ab8f4a03861b4f7a28cf` |
| `native-live-merge-r0168-originaljan11-a01/responses/r0168-loss-strengths-a01.json` | 443389 | `71569d346bb2a3bd82b498c11f50b552f8260f54c144425ec3d06cd0c4b7cd2f` |
| `native-live-merge-r0168-originaljan11-a01/responses/r0168-net-loss-after-a01.json` | 1054054 | `7a5a8ff069310a90ef997ce290fc956e8a6720c615e9c8029c22946e92c9a71b` |
| `root-r0168-net-loss-probe-a01/strengths-body.json` | 105008 | `25dfc31bcac34d7d9ae6234ca26c00afdfef5f39d5305f2f9920788189ed5cda` |
| `loss-cause/r0168-loss-current-readiness-a01/PAUSED-READINESS-RECEIPT.json` | 57080 | `200171c6b8123b5c4e5d1a639491b9b7733e05405ec328e2728b68bf6776f64e` |
| `loss-cause/r0168-loss-current-readiness-a01/ROOT-DELIVERY.json` | 2735 | `fba5a543d86b124e31cd8806d6ea3d33ba60709d51fb89e28c3a1aa80266807a` |
| `loss-cause/r0168-loss-current-readiness-a01/SOURCE-PINS.json` | 3067 | `4ee7efda01bd2325c97ce42ed184b521dcf1aeea442ae5f5d9789fd74ab71a1c` |
| `loss-cause/william-cf2-capability-check-a01/SOURCE-PINS.json` | 6031 | `5bec9cb8c21ae0754b6cc6d51f138d11c46886d1e7daffc2e1315817e72fdb65` |

Cf2 native_bridge / Python bridge 源码 pins 复用已完成有限源码核读，未重扫 EXE：

| producer/consumer（`ck3_autonomous_player`相对） | SHA-256 |
| --- | --- |
| `native_bridge/src/ck3_12003_adapter.cpp` | `efc5a577e2269d77101d1fc534f53231c725462e274bee28a4b0afcfdccbe507` |
| `native_bridge/src/ck3_12002_army.cpp` | `f39aee43ec7d2e154bb6196a6b832ee4dc817f3b17b8fd57551138f9445748b2` |
| `native_bridge/include/xar_bridge/ck3_12002_army.hpp` | `b76176e3d46de5696579728a5e64cbb9515a8ececa546a665375ed1844ccede7` |
| `native_bridge/include/xar_bridge/army_strength_v1_serializer.hpp` | `582d8445751a9691a056d0db61da787fd97193cd968d61426e18a23495dc4c9b` |
| `native_bridge/src/ck3_12003_army_replenishment_records.cpp` | `c9d88f514bf9f321b4731d265602cfa9c630ede8e33650e6a0a65a13213a99f7` |
| `src/xar_autoplayer/bridge/war_contract.py` | `bbdeff614cfa8e3f67cb506ff0891d779752ebcdcaf232d571200c38294da290` |
| `src/xar_autoplayer/bridge/mcp_server.py` | `c071154913b6e2e58028e379fcc3399f7872aded8365b18b7773eebbf9fa44a7` |
| `src/xar_autoplayer/bridge/service.py` | `08d379ea73939cf0dad148b097513f3cf8601af58fc0935b20643841f11c23a5` |

已完成外置 file-only JSON 对账使用主已验证 venv Python3.14.7，核 query/after body复制、同paused身份、所选缓存行、全部actual人数/上限sum与全 DATA覆盖，返回0。`open_kaishek=not-applicable`：这里沉淀 exact native CArmy getter与已采集 owning-thread读数，没有 parser/finite runtime可替代的执行语义。不重跑已有游戏/EXE/fixture，不把文档入库/CI当成新游戏日或新录像。
