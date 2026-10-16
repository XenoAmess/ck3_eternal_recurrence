# R09 下一场：特殊记录、实体 DATA 与单次受控合军

本轮是离线缺口复核，**没有新增 R09 实机、研究整卡或动态镜头资格**。读取机器 `machine_id: desktop-3fevhd2-1c74096080`；2026-10-16T09:59:31Z 用 `tools/ck3_live_run_id.py machine` 实际读回。审查基线 HEAD `20c7319b6964c80fa419540cf4e30852feff4810`；工作区其他 lane 的未提交改动不属于本页验收。目标历史证据为 CK3 1.20.0.4/build25734779、EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，本轮未重新读/哈希 EXE，也未连接 SDK、操作桌面、构建、导出或生成 EXE。

## 已有结论足够收窄问题

[R0176 selected93 微实际](episode04-r09-selected93-micro-actual-12004.md)已经证明：在日期53146632的同一正常生命周期内，93→独立发现的新162→93，一次拆分和一次原方向合军保持四个原 ArRg673–676 的实体 DATA 250/250；全部 available 军队的物理值及按 ArRg 的 DATA occurrence 同时守恒。93基线无统帅，162拆后及93合后实际统帅为34232。它没有新增空 DATA 1/1角色。

这批原件的 **strict unrelated freeze 仍是失败**：Army18 的1196/1196变为1195/1195，空 DATA、缓存1/1的ArRg59被移除。具名后验以真实 Character predicate、Character34232、140/148/F4/F8关联和独立统帅读数解释了这唯一例外；不改写原失败，也不把同类例外自动授给新场。available范围外16777321仍为 `native_carmy_not_found`，其兵力保持未知，不能填0或宣称全roster兵力通过。

已有 [actual .4 库存顺序](episode04-split-merge-stock-weight-order-12004.md)、[S端 flags0](episode04-merge-source-weight-flags0-12004.md)、[split完整体](episode04-split-half-source-12004.md)及[角色创建路径](episode04-merge-commander-character-record-producer-12004.md)，足够解释下一微实验需要测什么。**下一步优先补实测输入/结果与镜头，无须为开场再次扫描这些完整本体。** 不将源码已闭等同于现场执行PC已见。

## 最小未闭集合

| 缺口 | 当前边界 | 最小可接受补证 |
| --- | --- | --- |
| 独立反方向 | 只有selected93原方向。R176后继seed中的93已有34232，和旧baseline无统帅不同 | 从真正相同正常S0冷载的独立臂，split后以fresh sibling为D、原军为S，仅合一次；两臂完整可观测起点相同 |
| split和merge库存/容量/权重 | 小DATA投影不替代完整raw供给字段 | F0/F1/F2分别保存stock、cap、原生D weight、缓存current、独立实际统帅；按真实方向复算两阶段定点加权与合后cap |
| 动态镜头 | 微实际reader明确 `dynamic_video_qualification=false` | 新场30–60秒连续split→merge→survivor/统帅/队列/供给画面；对应原始时间线与实际端点均在片内，另做clean和完整观看验收 |
| strict例外复用 | 旧59/34232是具名、有限后验，非通用豁免 | 新差异逐FullID保存和解释；物理DATA、角色缓存、无关军队分别报告。未知变化不得删行或放宽旧结果 |

同一新S0若无法证明匹配旧F0，就要新forward、reverse两独立臂：每臂one split、one merge，共4个动作、6个必要strength端点。若实际取得且核同真正旧baseline，才可能复用旧forward、只新增reverse的2个动作。**从一次merge终态直接反转，不是独立反方向。** 已有pair的一次merge可以补库存公式样本，但不能补split→merge双臂合同。

真正 `upper_clamp_observed` 必须满足preclamp严格大于**合后实际cap**且实际stock精确吻合。不同precap/stock、等于边界、算式恰好吻合均不自动证明正量被截掉。若R09冻结卡只要求库存前后对比，普通nonclamp应如实入库；不得为追求阳性在看完结果后反复换将、改方向或重发。出生producer成功PC、全兵种永久枚举/全生命周期registry是独立研究边界，不应被偷偷加成所有DATA守恒观察的先决条件。

## 下一次必须保留的身份和兵类 DATA

这张表同时供视频取数与agent决策使用。所谓“特殊兵”不能压成一个可补员/不补员布尔。

| 层与键 | 每端点保存 | 禁止替代 |
| --- | --- | --- |
| public军与native军 | native roster CUnit完整FullID→typed CArmy完整FullID/generation；owner/control/province、同帧revision/nativeRevision/date/episode | ACK sibling、递增猜ID、用publicID冒充nativeID、把旧162写进未来场 |
| ArRg缓存 | 全部FullID、current/max/scale1、完整DATA状态、native Character predicate | 只看军队总人数；把1/1、type absent、空DATA直接叫骑士/事件兵/统帅 |
| DATA occurrence | ArRg FullID、record_index和原顺序、persistent完整FullID、physical chunk_index、observed backlink | 只取第一条DATA，或为守恒删掉重复别名 |
| unique物理槽 | `(persistent FullID, chunk_index)`去重求physical总数；current/max/state等真实值必须一致，chunk索引0–6 | 按record_index当物理身份，重复累计alias；仅总数相等代替身份/顺序/occurrence守恒 |
| Character角色 | 真实140/148、解析Character、predicate、F4/F8及读后同实例；空DATA行另列 | 用角色cache1/1推物理ADD、出生成功或Knight membership |
| 当前统帅与容量 | 独立typed `current_commander`；absent与unavailable分开；合后actual cap | 候选quality、movement preview、候选条件cap或两军原cap平均 |
| 补员分类 | 逐persistent联接真正fixed-chunk0 family：raw138/definition magic、native persistent bool、独立chunk bool、cached prepared148和fresh fraction | 仅MAA key/玩家兵名/缺额推Can；用当前false抹掉已缓存正F |
| supply与merge | stock/cap raw及scale；D用D getter，S用合前native current×100000；Province eligible另存 | stock/cap百分比、unique physical人数、S自己的D weight、CanReplenish替代merge weight |

alias有两种同时成立的计量：unique physical token只计一次；原始ArRg occurrence/record_index/顺序保持完整。相同token值冲突立即拒收；ArRg跨两个split军重复也拒收。迁移的是完整ArRg，原有DATA关系不能因新ArmyID便重分类。R0176的250/250结论还保留了全available occurrence，强于单纯总人数守恒。

[补员资格合同](episode04-special-troop-refill-eligibility-12004.md)已证明当前persistent raw138==1在Army/开关/资源之前直接拒绝；两native bool仍分别保存。普通split/merge/换帅不提供解除这道门的证据。**动作后必须重读当前分类**；R0176的raw1381/两bool false/cached1480只在baseline读过，不能从DATA守恒顺带宣称动作后raw138已再次取证。源码还没有给raw1382/3完整正式玩家类别命名，保留null足以做本次按对象判断，无需为命名另开全游戏研究。

S端actual `2A95720(flags0)`不做definition或supply-loss过滤，逐有效ArRg occurrence求缓存current。已证空DATA/cache1/1的角色对S weight贡献100000，对unique physical贡献0；不可补员不等于从S权重排除。这不授D getter或Province usage相同语义。D/S stock都取合前原值，选将和refresh先发生，再以实际postcap截断。

## 单次受控合军的验收次序

以下由Root独占已有正常会话执行，每步独立检查，不以脚本循环串动作。它描述现有typed接口的实际合同，不是本lane发出的请求。

1. 先冻结正常S0 SHA、实际source/loaded DLL、machine、PID/create-time、connection generation、actor/episode及容量资格。F0保持paused/map ready/无modal；保存全roster、complete普通strength/allDATA/role/stock/cap/weight和各available军独立统帅，末尾same-frame核对。不同冷载有各自PID/episode，不强求跨臂相同。
2. 如需新反向臂，先仅提交一次split，保存onceclaim、原请求和原ACK；独立F1从roster唯一集合差发现V，核U存续、两个不同CArmy generation及完整DATA。F1是该次merge的输入，不为补日志重复query；确实变帧或合法换将后才重新fresh premerge。每次动作都只按当次实际ID。
3. 此次固定反方向 **V←U**，只提交一次真实 `ck3_execute_step(step="merge-armies-<V>-with-<U>", expected_revision=<F1 revision>)`。fresh capability/具体step和原生Validate仍是条件；接口无独立公开split/merge legality preview，不能把广告存在说成CanExecute=true。
4. ACK后只读F2。独立确认V存续、U消失、其余roster不变、V原native generation保留；核全DATA/alias/occurrence、原ArRg和所有extra/missing、实际统帅、队列/供给、未改日期及lifecycle。先落完整observation再运行strict，失败也不能丢packet。只读后验未完成、超时或unknown时读取原响应，**不重发动作、不删除claim或换case绕过**。
5. 使用真实方向的wD/wS和合前stock，各军share先trunc0，再term分别trunc0，最后求和并按postcap clamp；保留fast域/overflow分支界限。物理/身份后验未过、字段缺失、零/负weight或native fallback域不授普通fast结果。精确nonclamp照实报告，不改这次结果。
6. 将selected physical守恒、角色变化、unrelated strict、all-roster coverage、库存公式、双臂S0关系和动态镜头列成独立结果。一个通过不能覆盖另一个失败。普通agent可继续合法OODA，实验冻结规则不升级为所有战争永久等待门槛。

## 现有消费者与实际可运行入口

可复用代码已经在正常目录，后续无需另外实现一套DATA reader：

- [身份/缓存/统帅消费者](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_merge_observation_12004.py)：`identify_split_sibling`、`compare_split_merge_cohorts`、`read_bound_current_commander`，拒绝stale/partial/duplicate；不会证明出生或补员。
- [物理运输断言](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_transfer_assertions_12004.py)：`assert_fresh_split_transfer_12004`，保留unique物理与occurrence双合同、独立统帅和角色变化。
- [当前补员消费者](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_persistent_refill_eligibility_12004.py)：`classify_army_persistent_refill_eligibility_12004`，联接现有allDATA/fixedchunk0；未知分类不填，cached/request/ADD分开。
- [R0176有限reader](../../ck3_autonomous_player/src/xar_autoplayer/bridge/episode04_r09_selected93_actual_12004.py)：`qualify_r0176_selected93_micro_12004`只接受具名59/34232例外，固定保留strict false、全roster false、birth false、dynamic false、R09 false。

仓库中现有离线重放命令如下；它只读字面小投影，不读取其中fullraw路径或发游戏请求。本轮未重复跑已验重放/单测，不新增信用。

```text
tools\.venv\Scripts\python.exe -B -O tools\validate_episode04_r09_selected93_actual_12004.py docs\ck3-native-ai\evidence\episode04-r09-selected93-12004\actual-literal-projection.json
```

[root_relay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge/root_relay.py)真实CLI有 `baseline/split-once/post-split/pre-merge/merge-once/post-merge/supply-clamp`、`--merge-destination sibling`、`--source-head`、`--run-sequence`和module pins；本轮仅 `--help` 实际exit0，无SDK或游戏请求。

**该relay目前不能原样用于新场。** 源码硬编码 `DEADLINE='2026-10-16T07:45:01.597+00:00'`，还核旧shared512MiB/new_scene_count1/deadline_extensions0。实际复核时间09:59Z已过截止，`Relay.request`会拒收 `original deadline reached`。`--source-head`/`--run-sequence`只解决新source/run绑定，不能延长capacity或绕过期限；没有已支持的deadline CLI参数。旧[NEXT-BUSINESS配方](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/split_merge/NEXT-BUSINESS.zh.md)须按这个现实边界阅读。Root须先按当前存储策略取得新鲜合法准入并审查相应执行器更新，才能宣布新场命令可执行；本页不改guard、不伪造现成新CLI，也不延长旧容量授权。

## 本轮新增与未新增

新增的是：将R09整卡最小缺口、角色strict例外、special/refill分类、alias双计量和单次反向merge后验汇成一个视频/agent共用入口；识别已有relay硬截止已过，避免重用历史配方造成重复空转。没有新增现场事实、来源PC观察、兵种枚举、全局兵力资格、native API、策略动作、SDK请求或视频审阅。

本页为小型`record`，按[统一存储策略](../storage-retention-policy.md)1.0.0的180天复核归纳；没有新增raw/save/压缩包/构建副本、永久保护或容量预留。新场大raw与录像仍由Root在重型写入前核当前机器、其他并发预留和各卷容量；历史deadline、路径存在或本文被引用不能续期保护旧资产。
