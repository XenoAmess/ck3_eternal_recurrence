# R191 研究卡与镜头信用窄审

- `machine_id: desktop-3fevhd2-1c74096080`
- 审阅时间：`2026-10-16T21:52:11Z`；运行源码：`60de49f61d23b9c3437af4544c3f12bb28445429`；场次：`desktop-3fevhd2-1c74096080--vanilla--R0191`。
- 本次只读小型衍生摘要与现行卡片，不重读三份 full Driver 或 raw 视频，不调用 SDK、游戏、桌面、构建，也不执行新矩阵。三端点分析：[ANALYSIS.actual.json](reader-derived-a03/ANALYSIS.actual.json) `13,451 B / SHA-256 3cd0507323451eec2bbecdf95951caba338e0303b7622ae4bbab4e1c1d2f3cd8`；[便携 ZIP](reader-derived-a03/R191-loss-three-endpoints.portable.zip) `14,224 B / SHA-256 56449ba71ddf6316e53159bdd1238d57be3f686938c96d7a08e65e93808cda3f`。同目录 [STRICT-SOURCE-FACTS.actual.json](reader-derived-a03/STRICT-SOURCE-FACTS.actual.json) 给出 callback 原件指针与 7 笔正 writer 的来源；原始 full 只保留精确路径/SHA 引用。

## 结论和边界

**这是一份已闭 R03 的独立、加强的实机补证，不新增整卡、核心业务或合格动态计数。** 当前仍为研究 `R00/R02/R03/R11/R12/R13 = 6/14 = 42.9%`，业务 `R03/R11/R12/R13 = 4/11 = 36.4%`，合格动态 `0/11`，正式 ABC `0/3`。现行计数以仓库 `docs/ck3-native-ai/episode04-current-execution-map-12004.md` 为准；R03 原卡已经由仓库 `docs/ck3-native-ai/evidence/episode04-r0177-20261016/r03-original-card-core-qualification.actual.json` 的 21/21 起点 DATA、7 笔实际 writer 扣 11、围城上下文等逐项闭合，不能再计第二张 R03。

R191 的 d0→d1 区间 `53148144→53148168`：同一 21 槽实体人数 `1174/1185` 不变，Army18 writer 正事件 0；虽全局序列增加 `0→283`，消费者没有声称全世界零损失。d1→d2 `53148168→53148192`：同一 21 槽实体人数 `1174→1163`、cache `1184→1173`，净减 11；全局 writer `283→513`，`oldest=2`、overwritten 增量 1 只覆盖 d1 基线之前序列 1，因此两个区间的**各自必要保留范围**均 complete。严格生产消费者给出同一个 callback token 8 的 7 笔正物理 writer、合计扣兵 11，且 7 笔均有 siege-only budget source 绑定；当前场次的围城来源比旧 R0177 的上下文归因更直接。这里的“完整”只指两段已审 Army18 fence，不声称全世界所有事件日期、其他损耗阶段或完整区间总账；单事件 exact 视频 PTS 未建立。

R11 是未锁定 Halt 的研究负控，R191 没有 Halt/路线动作，不增加或改变 R11。R04 县界、R05 零库存、R06 补员、R07 登船双臂、R08 实付费用、R09 拆合军、R10 三臂等均没有各自必要的新动作/对照/原生结果；尤其 R191 stock/capacity 始终 `30000000/30000000`，不能算 R05。R03 新分析里的 `R03_full_card_or_media_qualified=false` 表示 **R191 单场没有另行签出整卡或镜头**，不能拿它回退已入库的 R0177 R03 研究核心闭合。

R191 [film result](D:/workspace/ck3_native_war_ai_promo_work/e04-r191-window-capture-a01/r191-film-a01-film-result.actual.json)记录 2 天、wall `115.0005729 s`，其中暂停尾段 `82.9820883 s`、83 次只读快照和零额外 Resume；[raw recorder result](D:/workspace/ck3_native_war_ai_promo_work/e04-r191-window-capture-a01/raw-window-a01/result.json)记录前景 CK3 客户区 1280×720、normal recorder exit0、`clean_spans_certified=false`、`human_approval=false`。另已只读 [bounded media audit](D:/workspace/ck3_native_war_ai_promo_work/e04-r191-media-audit-bounded-a01/audit.actual-a01.json) `19,453 B / SHA-256 52ca8dc34420a5912235f28c714fd5a6540d9362f710542556a2218583849dfb` 与其 [portable facts](D:/workspace/ck3_native_war_ai_promo_work/e04-r191-media-audit-bounded-a01/portable-media-facts.actual-a01.json)：3359 帧、编码 `111.966 s`、完整音视频解码 exit0；这项后验审计解决录制收据当时的 `media_probe_pending`，但四格抽样不等于完整人工 1× 或 clean 认证。暂停尾段不能称连续自然动态；业务 writer 到具体画面 PTS 未绑定。R03 镜头 M 可列为后续对帧候选，**合格动态仍 0/11**。

录像与研究叙述可以说“R191 的两日独立实机中，第二日 Army18 的 7 笔同 callback 围城来源物理扣兵合计 11，物理总数 1174→1163”；不能说“这 11 人已在经审定的视频时码可见”、全世界零其他损失、R05饥饿、R08已付款，或新增第七张研究卡。智能体可消费严格物理正事件与 bounded fence，不应把它升格为完整损耗预算或一般化每两日必减 11。
