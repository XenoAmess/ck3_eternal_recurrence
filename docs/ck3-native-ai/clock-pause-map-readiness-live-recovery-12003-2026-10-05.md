# CK3 1.20.0.3：暂停/恢复地图的真实推进恢复

2026-10-05。Readiness 为有限 **production-live loop**：Robert29829 原普通战役的 exact24h 推进、独立暂停帧和正常保存已恢复。原生链与修复定义回链 [clock-pause-mcp](clock-pause-mcp.md)；本记录复用已冻结的研究，不改变策略或新增调用。

运行绑定为 **v72/g77/R45**、source `f26be866fcb1642b81ffbac4707fdc447db1e068`、episode `native-29829-2bc2d599f7f9`，CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`；普通战役 XAR off，environment SHA `ae8140b0e434747c57b2a6223b0602b34c9d49e2ba60df5619f8057bed4aeef9`。

- 两个 disjoint SDK 包 **13745/50443 均 CLOSED0 GREEN**：先实际恢复1日，raw53263128→53263152；再实际19日→53263608。合计 **20 whole/calendar/bounded 日、480 raw小时、partial0**，140 GREEN工具叶＋20 day results＝160 daily原JSON；不把恢复1日重计为第21日，也不把原planned预算算日。
- 本 lane 对 combined FULL cache 仅一次完整消费。20轮均有 fresh priming、accepted set-speed/resume/pause、实际独立末帧 +24 raw小时、paused/map_ready=true 和匹配的 normal SAVE。推进成立由实际日期增量与独立保存共同证明；receipt未另发布独立 unpaused snapshot，不能仅凭 resume ACK 代替真实推进。
- 正式计数 **4950→4951→4970 / 36524**，resumed1797→1817、Oct5/W41 +292→+312；此前日数与R44旧失败均不重复增量。末帧 **native85/public77/raw53263608**，Robert alive、paused/map_ready=true、event/interaction null。
- 恢复1日 normal **h8757/raw53263152/98330892 bytes/SHA `95e51a0bb3515d8ed60061cba3e033311b6a752eb0f86d7c1025127d388be88c`**；其后19日末 normal **h8814/raw53263608/98508483 bytes/SHA `2f58f4a612e7d774fdb0e43ab23c6b325b07b027cacf540d4e0b2e339c16e1aa`**。这些是不同 actual saved anchors，后来零日查询保存不替代 whole 日计数。
- 原 **R44 day03 zero-day RED** 仍保留：`life-advance-one-day` 返回 `native gameplay step failed: CK3 map state is unavailable`，原before/primed/after同raw53263128，失败日增量0。P0 source fix `a6f4a4fc5581af48f7b061c06f953722c47627ea` 将 Worker pause/resume 命令使用范围收回 exact-build 八项 Core 字段，保留 owner/TLS/date/paused、核心一致性与 TimelineReady/Queue、公开 revision；未把命令局部Core投影发布成完整状态。知识记录/frozen source为 `f26be866fcb1642b81ffbac4707fdc447db1e068`。
- 本轮20次实际推进证明修复后 bounded ordinary advancement 恢复，不能反推旧失败的具体拒绝类别、失败 full-snapshot 子域或永久通用故障消除。源级解释、已通过的独立生产路径 case 与 full build 直接复用，不重跑旧测试。
- 器械公共军268435481尚未目的地470；两支既有主军/guard围城继续，own combat/retreat仍0、War117440524 active/+25。新增 **470到场、有效器械围城贡献、battle、war victory、natural succession、completed family 均0**。当前边/剩余日与470同帧M/K/D由Root后续 fresh query 的各owner实读；daily generic null/旧丰富基线不互相回填。

唯一 combined frozen输入：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v72/root-results/v72-current8751-01/ordinary-r45-firstedge-twenty-consumed01/FULL-TWENTY-DAYS-CACHE.json`，**15101484 bytes / SHA `28efafe7752abf2be988ec5583092c3a56bb52ead8c1fb4daf113720cb906eb6`**。同目录 `receipt-topic-lane/report-fields.json` 与 `RECEIPT-LEDGER.json` 保存20轮收据、每个raw/date/SAVE pin及未完成边界。父owner对160原daily JSON各完整消费一次；本lane没有读原JSON、调用SDK、占用窗口、修改共享源码或Git、运行full build。后续实际到场和战争结果仍由新的真实暂停帧验收。
