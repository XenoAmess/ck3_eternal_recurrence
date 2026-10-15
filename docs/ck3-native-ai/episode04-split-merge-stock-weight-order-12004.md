# actual .4 拆合军：库存、角色权重、选将与容量截断

本增量只核已持有的1.20.0.4/build25734779原始指令与现有消费者。来源机器 `desktop-3fevhd2-1c74096080`；EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518` 复用原资格，不重新读或整哈希EXE。研究时源树d9322bcfb3e17a3fe78607cea777bbfaf7be0a11；实际时间与各原件pin在相对 [source-index.json](evidence/episode04-split-merge-stock-weight-order-12004/source-index.json)。它携带4个完整held raw body的hex和选定指令片段：merge4161B、clone720B、split2819B、capacity1545B。选定片段不是完整反汇编；原件缺采集时间的字段保留null，本次读held文件的时间不冒充原采集时间。无新SDK、现场、游戏日、EXE读取、构建或主树写入。

这给 [早期R09页](episode04-special-troops-split-merge-12004.md) 中“当时只引用.3完整加权树”的历史边界增加具名actual .4证据；不是将旧.3地址平移，也不把源代码结论算成R09实机完成。原 [角色producer](episode04-merge-commander-character-record-producer-12004.md)、[拆分普通体](episode04-split-half-source-12004.md) 和 [R0176微实际](episode04-r09-selected93-micro-actual-12004.md) 的范围各自保留。

| 对象 | actual .4 指令与计算 | 消费含义 |
|---|---|---|
| split库存 | `296C364→296B6C0`；clone的`296B936`读来源CArmy180，`296B93D`原样写新CArmy180 | child stock等于原stock，不按人数比例除半；原军同字段未被该copy改写。clone里另有CUnit180的相同offset读写，不能混为CArmy库存。 |
| split时钟/容量 | `296B928/92F`复制188，`296B944/94B`复制190；之后搬整条ArRg、分别`296CC85/94→24E8100`，再选择/清角色/任命新军统帅 | 旧锚复制不授新grace；stock复制不意味着两军capacity相同，不意味着最终stock已低于child cap，也不把临时分组权重当持续chunk平分。 |
| 目的军D角色权重 | `2C55351→24E0140(D,out,0)`与`2C55363→24E0280(D,out)`，`2C55368/6B`相加 | 使用该军**作为D时**的native `merge_supply_destination_weight_raw`。 |
| 被吸收军S角色权重 | `2C5576F`取S的ArRg向量38，`2C55773`置flags0，`2C55775→2A95720`，`2C5577D`乘100000 | 当前provider的`current_soldiers`正由同一native getter并与完整ArRg sum核验；S用这个值×100000，不用S作为D的字段，更不用post总人数或unique physical DATA和替代。 |
| 原库存捕获 | D在`2C55413`读180，S在`2C5583E`读180，先存入并列临时weight/stock数组 | 后续算式消费合军前各军原stock，不用角色改动后或post stock回填。 |
| 合后容量 | `2C55FBE→2C53BF0(out,D,null)` | 此时已经完成选将/任命与D composition refresh；使用合后实际current commander的容量，不合计/平均两军原cap。 |

“eligible权重”在这里是merge角色getter的真实数值，不是Province用量的 `native_supply_loss_eligible`，也不是补员permission。两个D getter的内部完整predicate列表不在本增量重闭，因此不能由类别、headcount或Character predicate手工重建D。生产 `ck3_12002_army.cpp` 的provider还核两返回指针、非负及D不超过该军native current×100000；这些只读观测映射由 `ck3_12004_army_support.cpp` 精确绑定24E0140/24E0280。物理DATA去重合计、ArRg缓存合计、D weight、S weight四者应分别保存。

后续[actual flags0完整路径](episode04-merge-source-weight-flags0-12004.md)补闭S端：2A95720在flags0绕过definition筛选与supply-loss-eligible调用，直接逐有效ArRg累加缓存38。因此空DATA/cache1/1角色在S权重贡献1，不可补员special也不因permission false被排除；这不授D getter同样语义，也不授实体补员。

merge普通体先收D、后收S的weight、stock和有条件的commander候选。`2C55A3E→24DF9F0(S,-1)`清S统帅，再以`2C55AA8→24E0D10`、`2C55AB2→24E0C50`迁移原完整ArRg。候选选择后，`2C55E74`可先清选中角色原军的统帅，`2C55E7F→24DF9F0(D,selected)`写D统帅，`2C55E93→24E8100(D)`刷新，然后才进入库存计算。D与S候选准入分支不同；仅“先D后S”的收集顺序不证明所有排序分支同分必选D，质量高也不等于cap高。此处不重授排序helper内部tie语义，现场仍要独立读实际统帅。

令SCALE=100000，wD是上表D返回和，wS是该次S native current×SCALE，W=wD+wS。当前两个正权重的普通fast路径为：

```text
shareD = trunc0(wD * SCALE / W)
shareS = trunc0(wS * SCALE / W)
termD  = trunc0(shareD * originalStockD / SCALE)
termS  = trunc0(shareS * originalStockS / SCALE)
preclamp = termD + termS
postStockD = clamp(preclamp, 0, actualPostCapacityD)
```

`2C55F13/16`跳过weight≤0的term；通常正W路径在`2C55FE0/FE9`做share的乘100000/有符号除法，`2C56099..AE`做term乘法/截零，`2C55F7D`累加。`2C55FBE`返回cap之后，负和先归0；非负和在`2C560B6/B9`与实际cap比较并上限截断，`2C560BD`最终只写D180。两个share之和可为99999，不补齐，不重归一，不化为一次浮点平均。零总weight、负值和编译器大值fallback分支不能套这条简式当已验native结果。

实际机器码会选择overflow保护分支：`2C55FD7..FF4`对正numerator上限 `0x53E2D6238DA3` 作fast-div guard，`2C5607F..93`对两个乘数各以 `0xB504F333` 作fast-mul guard。超过时存在分解/大分母路径；无限精度Python直算不能直接冒充它。本增量给a03 `compare_merge_supply`加这两个输入边界，超界返回 `HOLD_NATIVE_FIXED_FALLBACK_BRANCH`，不给upperclamp资格。当前stock100/300与约250/1195人的seed资料远在fast域内；该资料仍须在新scene读回。只增加1项定向边界检查，不重跑原4项relay检查。

capacity的actual `2C53BF0`先从CArmy120解析有效Char，再在`2C53C7D→28C3AC0`取该角色aggregate。`2C53C97`/`2C53D08`分别查modifier467/468，缺项为0；FULL来自实际loaded `5C68C70`。普通表达为 `native_qmul(FULL+modifier467, SCALE+modifier468)`，有独立大值fallback；无有效Char则`2C54154/15B`直接输出loaded FULL。null detail在`2C53E13/16`走`2C540CC`输出分支，没有把UI详情容器作为数值依据。candidate optional容量leaf也只能是“按此角色当前aggregate的条件容量”，`assignment_applied=false`；任命后的aggregate、实际current commander和cap还要fresh读回，不能拿候选质量或条件值代替实际应用。

库存“复制”、合军“加权”、合后“选将容量”、最后“clamp”是四个不同步骤。相同库存的两军未必在raw上原样恢复，因为分阶段截断；不同precap不保证clamp，因为实际选将可能使postcap继续为300。只有独立动作后验通过、同日完整physical DATA/occurrence守恒，并且 `preclamp > actualPostCapacity` 且实际stock exact吻合，才能为该次positive fast分支记upperclamp。相等边界不是上限截掉了正量；算术吻合也不等于抓到源PC执行。

最少动作应按待回答问题选，不为了补日志重复已验微实验：

| 待回答问题 | 最少独立普通动作与读数 | 不能顺带授予 |
|---|---|---|
| 对既有同地两军，仅区分D←S与S←D | 从同一正常seed分别cold-load两个arm；每arm一次fresh pre-merge packet→一次merge→一次fresh post packet。共2次merge、4个必要strength端点；已有同帧完整packet直接复用，不再补同义query。 | split行为、同一存活军的连续reverse、必有stock差异或upperclamp |
| 比较split后的两个合军方向 | 同S0两个独立arm，各baseline→one split→fresh唯一sibling及完整DATA→one frozen-direction merge→fresh后态。共4个动作、6个必要strength端点；不额外取pre-merge，除非中间确实合法换将或帧变。 | 从第一次merge终态立即反转便当第二arm、把历史162写成未来child |
| 只补一次真正upperclamp样本 | 优先复用已存在不同stock/实际cap的合法同地pair，fresh输入后只merge一次；若preclamp不高于postcap，保留真实nonclamp，不重发。 | 由stock300与100就预言clamp，或事后换将修该次结果 |

每端点用现有ordinary全scope Strength保留全raw引用：available目标的完整ArRg/cache/DATA/role/stock/cap/D weight，与独立typed current commander；fresh snapshot/caps须同revision、date、episode与PID/create/gen。新Army只取独立roster差分并核CUnit→CArmy完整generation，动作ACK不供身份。不同cold-load的PID/episode应各自新绑定，不能跨arm强求相同PID；共同seed SHA、日期/省份、owner、原cohort/DATA、stock/cap、实际统帅、战争/命令状态及实际构建必须按冻结合同核同。

R176后继seed的93已由34232统领，旧R0176微实验baseline的93无统帅。只有原正常seed及完整可观测baseline确实匹配旧arm、且构建/运行资格被Root接受时，旧forward才可能复用，仅新增一次reverse split+merge；人数250相同不足以复用。否则采用新的同S0 pair，不将旧forward与新reverse拼成已闭比较。原Army18 ArRg59→Character34232的strict例外不自动迁移；新global角色变化先保存完整packet，唯一解释后再另授有限资格，不重发未知动作。

当前R0176只证selected93单向拆合250/250及具名角色变化，stock/cap/weights完整实机公式、独立反方向和动态镜头仍由Root下一scene补齐。R09整卡和视频clean/human签核保持false。本页可给视频讲源码的真实顺序、给agent选择最短实验；不能被字幕写成“当前.4 upperclamp已实测”。
