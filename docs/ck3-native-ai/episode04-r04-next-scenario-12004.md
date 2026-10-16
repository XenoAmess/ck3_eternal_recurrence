# Episode 04 R04：下一条正例县边的最小条件

R04 现在缺的最小实机输入是：**一条新鲜、合法、实际第一边的 `24E2230=true`**。不是再读一次预算，也不是再把 Army18 沿已证 false 的路线推进。R182 已把两条边的拒绝位置收窄到第一次 target P；R183 没有新增路线，不能增加 R04 资格。

本次离线审阅机器 `machine_id: desktop-3fevhd2-1c74096080`，观察时间 `2026-10-16T09:01:17Z`，源码基线 `20c7319b6964c80fa419540cf4e30852feff4810`。机器 ID 来自当次 `tools/ck3_live_run_id.py machine`。本包只读共享源码、文档及已有小型研究摘要，无 SDK、桌面、游戏、EXE 读取、构建或大文件导出；只新增本文。现有 raw/save 的继续保留与容量由[统一存储策略](../storage-retention-policy.md)决定，本文不续期旧配额或资产保护。

## 本轮新增的源码关联：Q 已有共享来源

县专题此前将邻接 `Q=2C097F0` 列为未展开，但同一 exact `1.20.0.4 / Steam25734779` 的[补员位置研究](army-next-route-replenishment-position-condition-12004.md)已持完整 `[2C097F0,2C099C1)`、465B 本体。其来源 SHA 为 `2d18c1c2179d6e29d0252760c1cde9287064156905860592729969fd81d93a95`，由[方向关系专题](army-position-relation-2c09410-12004.md)记载；EXE SHA 同为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本轮没有重新采集该 body。早期专题未给出可靠的原采集机器 ID，因此这一早期 Q 采集记录的 `machine_id: unknown`；这里复用其源码合同，不把它当作当前机器的运行或安装资格。

仓库现有 [PositionPolitical](../../ck3_autonomous_player/native_bridge/src/army_regular_core_passive_12004.cpp) 的开头保留 exact 原分支：`actor_id == holder_id` 立即 true，注释定位 `2C09817`。其后还消费同侧战争、双向关系、holder 向 actor/同侧参加者的链以及[最终 holder→actor 谓词](army-position-2c3a0e0-readonly-12004.md)。这些不是本轮新解码的 body，也不在本文重新命名为通用军事通行规则。

将这一已持来源与[县条件完整结构](episode04-county-entry-condition-12004.md)串接，可得到新的、有界路线约束：

```text
mode1 的最终县条件 true
  => source P、target P first、target P second 都实际 true
  => 对 targetCounty 集合中每个 nonnull N，Q(actor,24D4ED0(N)) 都 false
  => 不存在一次实际邻接 helper receiver 的 full Character ID 等于 actor full ID
```

最后一行是上述源码组合的**必要条件推导**，不是某个 R182/R183 邻居的实测。只要取得同次实际邻接 receiver full ID 等于 actor，就能排除该县边；没有这些身份时仍为 unknown。不能用地图邻县的 legal holder、occupation side、同 realm 或 county title ID 代替 `24D4ED0(N)` 的实际返回。

还应避免一个容易误用的复用：现有 [next-route 补员 leaf](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_next_route_replenishment_position.hpp) 也调用 `2C097F0`，但第二参数来自 **Province-holder getter `247D010`**；县邻接第二参数来自 **County helper `24D4ED0`**。同一函数 RVA 不意味着同一 receiver。没有同帧实际对象身份连接，不能拿 `native_first_target_position_eligible=true/false` 填县邻接 Q，更不能跨 query 连接 opaque County 地址。

## 当前证据把缺口缩到哪里

| 来源 | 已证事实 | 仍缺什么 |
| --- | --- | --- |
| [R182](episode04-r182-march-and-county-p-12004.md)，2644→2637 | 双 definition 非零、异县；source P true、target P first false；后两层未执行 | 一条 target P first 能通过的不同第一边；此边不能继续贡献正例 |
| R182，2635→2634 | 同样在 target P first false 短路 | 不能因省份变了就视为已取得新的条件类别 |
| R182 War4 occupation 表 | 当时 defender holdings 为2635/2636/2644，均 county2191；2634为 attacker county2196 | 新场重新读取的候选表，以及不同县的真实 firsthop；旧表不保证当前态 |
| [R183](episode04-r183-window-capture-12004.md) | Army18 在2635围城、完整空路线；三次自然日推进；录像为截断 partial | 没有本场新行军、县进入或 writer 正减 |

War4 表原件为 R182 `responses/r182-war-a38-04-targets.json`，观察 `2026-10-16T04:56:24.879949Z`、89730B、SHA `430d8634d527f28f7c475a6fb706a93d58dc7fed0abeae61f5fd392bf9ccbc4f`，来源机器为上文机器 ID。本文没有重新读/复制这个原件；从 Root 已持的 `r183-route-offline-a01/R183-ROUTE-RESEARCH.md` 引用其精确小摘要。其他机器不能由该表获得当前战争态。

这里有两个不同层次的“最小”：解释 R182 false 已有实际 target P first false，继续追 Q 不会改变该次短路；寻找下一场正例只需取得原生最终 true，不必先完成所有关系 helper 的正式语义。若未来三次 P true 而最终 false，才把下一轮解释缺口转到邻接 Q；[现有 trace consumer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_predicate_trace_contract.py)已区分该源码推断，不能把它记作某个邻居 Q 的实际返回。

## 下一场有界请求与停止线

Root 完成当次机器、容量、Steam 离线、运行身份和屏幕租约检查后，保持暂停，执行以下有限顺序。本文没有提交这些请求。

1. 一次 fresh snapshot，确认 actual actor、episode/generation、Army18 的 public/native FullID、owned/controllable、非 combat/retreat、实际起点/完整路线、date/revision。当前不是2635或战争改变时，旧五个省 ID 只能作为历史种子。
2. 对**当前实际 active war**读一次 `ck3_query_war_occupation_targets_v1`，要求 available/collection_complete；结合当次 capabilities 产生合法目标。unavailable 不能当空集合，旧 War4/敌方抬军点不能替代当前准入。
3. 若仍是同一局面，只读 preview 最多五个已有接口来源的目标 `1032、1036、2624、8645、8653`，每目标至多一次；若有新的原生目标表，则优先其实际异县候选，仍不超过五个。每个成功结果先经 [strict first-edge normalizer](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_county_entry_preview_condition_contract.py)；按同一 frame 的 `(actor, mode, actual origin, first remaining hop)` 去重。多个远端终点导向同一 firsthop 只算一个条件，不反复探测。
4. 只有 strict child available、完整 firsthop 绑定、双 definition 非零、原生最终 `native_condition_passes=true`，才进入正例候选。available false 是该次负控；unavailable 是未知。trace 缺席不损害已严格绑定的最终 bool，但不能声称已解释内部原因。
5. 最多五个 preview 后没有新的 true 第一边，就结束本批 R04 搜索；不提交 Move、不靠自然推进碰运气。某条三 P true/final false 时，也停止该边并保存为邻接缺口，不能现场扩成无上限地图扫描或新 hook。

同一 frame 已失败的两个边不为提高调用量重复测试。日期、actor、军队、source 或政治态改变后，旧 false 不自动排除新 frame；这是下一批重读理由，不是本批重复理由。

## 可复用决策与真正验收

供视频和智能体共同使用的三值口径如下；`preview_candidate=true` 只表示可以继续核执行门。

```text
preview child 未严格绑定 / unavailable -> preview_candidate=unknown
strict available 且 native final false -> preview_candidate=false，保留实际 P 拒绝槽
strict available 且 native final true  -> preview_candidate=true，actual_county_loss=false
```

正候选仍须按[现有自然正例合同](episode04-county-natural-positive-scene-recipe-12004.md)验证：当前 B>0、typed Unit/Province、真实 conditional arrival special flag 为0、同帧 whole/S_pref、writer 安装及 pre sequence/failure fences。优先 `S_pref>=B` 的 primary-only 观察路径。然后由 Root 对真实 firsthop 一次 typed Move，以**后验 stored route**重新核 condition，才自然推进一边，到达即暂停。unknown 动作不重投。

R04 positive 最终需要同次县 writer `caller_return_rva=0x24E25EE` 和 unique physical DATA 槽正减；残差另需精确 county parent。严格消费继续复用[现有县 writer consumer](episode04-county-entry-loss-12004.md)。本轮没有发现必须修改该 consumer 的新证据，故不改源码、不补 synthetic 资格、不新增单测。预算、兵数净变、condition true、补员位置 true、围城 tick 或可见录像均不能替代该 physical 证据。

本轮新增的是“县邻接 Q 与既有补员位置源码是同一 body、但 receiver 来源不同”的可复用知识，以及由 full-ID equality 分支推导的必要排除条件。没有取得新的实机 true 边、县扣兵、clean span 或 R04 百分比信用。
