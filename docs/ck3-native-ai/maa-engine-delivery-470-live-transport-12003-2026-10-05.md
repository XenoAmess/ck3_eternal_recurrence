# CK3 1.20.0.3：器械军到470的真实运输闭环

2026-10-05。Readiness 为有限 **production-live loop**：既有单次派遣后的 retained route，经日级独立观测和正常保存，实际交付器械公共军268435481到目的地470。暂停/恢复原生链回链 [clock-pause-mcp](clock-pause-mcp.md)，此前20日恢复回链 [clock recovery](clock-pause-map-readiness-live-recovery-12003-2026-10-05.md)；阵容与围城效率输入沿用既有 army-composition/siege-efficiency 专题，本记录不改策略、不新增MCP。

运行绑定 **v72/g77/R45/source `f26be866fcb1642b81ffbac4707fdc447db1e068`**；Robert29829、episode `native-29829-2bc2d599f7f9`、普通战役XAR off/environment SHA `ae8140b0e434747c57b2a6223b0602b34c9d49e2ba60df5619f8057bed4aeef9`。Exact build 为 CK3 1.20.0.3/Steam25652598/EXE SHA `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

- 新的三个 disjoint SDK **14668/20699/37186 均 CLOSED0 GREEN**，实际1＋1＋10＝**12 whole/calendar/bounded日、288 raw小时、partial0**；raw53263608→53263896。84 GREEN工具叶＋12 day results＝96原daily JSON，各轮实际+24h、独立paused/map_ready帧、匹配materialized normal SAVE。
- 正式计数 **4970→4982 /36524**、resumed1817→1829、Oct5/W41 +312→+324。此前P0恢复20日仅历史引用，本轮增量不重计；恢复至今32日只是20＋12汇总。Resume ACK由真实日期变化和SAVE后置验证支持，不代替它们。
- 首次实际470到达位于 combined day **12**（batch `final_ocean_edge_ten` / day10）：before **raw53263872/native139/public38**，engine268435481@8652、state4、route[470]；独立 after **raw53263896/native142/public41** 与本轮final均见 **@470/sieging3/route[]、noncombat/nonretreat**。到达由两个真实后置观测与同日normal SAVE确认，未重发move或从旧ETA推日期。
- 首次到场 normal **h8857/raw53263896/98687773 bytes/SHA `b3b9e84e1e4617933ec89e0e7834fa709b9fb5a3545a7a7edf57f601f0384e1a`**；末whole normal **h8857/raw53263896/98687773 bytes/SHA `b3b9e84e1e4617933ec89e0e7834fa709b9fb5a3545a7a7edf57f601f0384e1a`**。同一保存文件以后被其他零日查询覆写时，历史whole anchors仍独立保留。
- 末独立帧 **native142/public41/raw53263896**，paused/map_ready=true，engine268435481@470 sieging3、emptyroute、无combat/retreat；War117440524仍active/+25。本段只授器械军到场/交付闭环，不由 generic soldiers=null、库存tier2或围城状态推出实际K、M、D或新增攻城贡献。
- **有效器械围城贡献、围城完成、battle、war victory、natural succession、completed family新增信用均0**。Root独立 rich query21083 与regiment/army观测由其他owner消费，用其同帧字段确认贡献；本lane不读取该原件，不回填daily缺失丰富字段。
- 旧R44 day03 `native gameplay step failed: CK3 map state is unavailable` 的zero-day RED仍保留；source fix `a6f4a4fc5581af48f7b061c06f953722c47627ea` 与此前20日恢复不重跑。后续32日实际推进不反推出旧失败具体拒绝类别、失败full-snapshot子域或永久通用故障已消除。

唯一本轮输入：`Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/runtime-preparation/v72/root-results/v72-current8751-01/ordinary-r45-engine-transport-twelve-consumed01/FULL-TWELVE-DAYS-CACHE.json`，**9377545 bytes / SHA `82f5d1266354256f4fe5a686593a37f6f190769a1d049b891bc77aaf22434b91`**。同目录 `receipt-topic-lane/report-fields.json`、`RECEIPT-LEDGER.json` 保留12轮日期、七叶pin、normal SAVE及首次到场切片；父对96原daily JSON各完整消费一次，本lane仅完整读该FULL一次。没有读旧20日cache/patch、调用SDK、占用窗口、改共享/Git、跑测试或full build。
