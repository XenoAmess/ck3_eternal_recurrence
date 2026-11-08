# P159：移除 token 切片仍有回退代价，默认 PARK

本候选只把新增的非权威 DATA matcher 从 token 副本比较改为原 body 的区间比较，机械保留既有 TOKENS／导航／offset／skipChildren／finishToken／边界语义。原 private stateToken、factory、parser、Guard、hash、oldencode 体逐字不改。4MiB 仍只是优化否决；完整 packet 严格解析、envelope、原 64MiB 接受域和失败后的旧编码比较／完整 state parse 均保留。expected 首尾不是 `{}` 时直接 miss，不是 JSON 拒收规则。没有 token 切片不等于没有扫描、编码、拷贝或峰值风险。

A 是 currentP150 Reader＋Assembler 与 P143 Driver3；B 是新 Reader4＋已闭但未采用的 P158 Assembler6＋同 Driver3，两侧各13类隔离并逐类核来源，parent DTO／contracts Decimal共享。B是新组合候选，不能把跨单元数字当同输入A/B。仅必要 Reader1TU4、Test1TU4和sole JUnit实际0／accepted／CLOSE释放，1P0skip；没有重编或复制Assembler／Driver／旧App／Main／SDK，也没有新profile。

唯一保留报告74,356B／SHA256 `c6d5733480b6dd246ee641031698f3fc12cc5e0713d5deb18757a5ede1a06f50`：先保持P158原三形态输入字节及96次顺序，再追加compact packet／内部pretty actual state的32次硬miss，四形态各8ABBA／16A16B，共128。全部端点、完整typed／member order／canonical bytes／原件SHA后验通过；17功能case／34次公有调用和8个DATA probe通过，含1001digit窄parser miss仍旧接受、包嵌套64正例／65同类同消息拒收、>4MiB旧路与多故障顺序。@TempDir.NEVER＋CREATE_NEW，0setup target／0额外warmup，所有冷首和后续暖行保留。

| 独立输入 | allocation mean A→B，B/call | wall mean A→B，ms | wall median A→B，ms | 八配对wall B−A |
|---|---:|---:|---:|---|
| compact exact | 50,880,733→50,886,872 | 14.6741125→13.3848 | 12.86535→10.1383 | 5负3正 |
| pretty exact | 91,552,021.5→50,874,445.5 | 18.309325→10.3056125 | 16.76085→9.90855 | 8负 |
| 外侧空白miss | 91,551,242→91,551,261 | 19.50320625→20.86316875 | 16.3745→16.8257 | 4负4正 |
| 内部pretty硬miss | 91,551,464→91,552,352 | 16.07459375→18.34019375 | 15.73895→16.4823 | 2负6正 |

pretty分配−44.4311%、wall mean−43.7139%，两项8/8配对下降，保留为条件事实。compact wall mean−8.7863%但仅5/8配对下降，allocation mean反而＋6,139B；7/8分配配对下降，首cycle＋113,072B驱动均值，归因UNKNOWN，不能称已证初始化成本。外侧miss wall mean＋6.9730%、分配近乎持平；内部硬miss wall mean＋14.0943%、6/8更慢，每调用精确多888B且8/8分配配对增加。这个反例需要完整token扫描后再旧回退，不能以外侧空白的早否代替它。

current-thread CPU累计compact187.5→125ms、pretty250→203.125ms、外侧miss265.625→187.5ms、内部miss234.375→203.125ms；存在0及15.625ms量化，compact B median7.8125ms也是两档中位值，其余median15.625ms，不授可靠CPU百分比或零cost。自然输入频率未知，各形态不合并headline，不用pretty-only取代当前compact和miss目标。Root最终DEFAULT_PARK，current350仍P150；Source／Test保D，不正式采用、不回滚已发表生产、不补样本。

setup2.0147569秒、功能0.1384398秒及before-report5.1113379秒保留，后者不是完整进程或准备窗。三个actor合16.8538545秒／operator资源子窗合20.0963908秒，不替代准备与等待；JUnit actor7.8357411／outer8.8782125秒、child stdout481B／stderr295B保留。metadata1,079,370B＜4MiB、报告＜256KiB；预算通过不等于整个parent瞬时硬峰值通过。

更早已知Root契约／D授权锚 `2026-11-08T20:36:32.931219Z`→末CLOSE1292.409587秒／→资格1454.531636秒／→后到决定附记1502.294397秒，包含实现、深度假设纠正、源码与测试审阅、准备、冷启动、等待和后处理；此前UNKNOWN，不记0。Native后起的1226.4192／1388.541249秒只是子窗。0新增SAVE，不报有限秒／保存日，不授Runtime、whole worker、10秒或peak收益。

本次正常只发表unit／daily11-09／weeklyW46三事实文档。P158与P155／156 PARK、P152原失败及P141预算失败均不改；P160仅独立D候选准备，不捆本发表或回填旧数据。

原件：[Native最终资格](D:/ck3-state/resume91-native-integration/p159-token-range-prod01/QUALIFIED-P159-TOKEN-RANGE-PUBLIC-STATE-FIXED128-SOFTWARE01.json)（49,286B／`38f02bf3c6b6752c18fe29c3ced8af4b46a00d162a4cb7133bc6d334cecc1a9c`）；[全部128行](D:/ck3-state/resume91-native-integration/p159-token-range-prod01/tmp-junit/junit-4717119539919258361/p159-original-state-token-range-fixed128.json)；[Root最终159原件核验](D:/ck3-state/resume91-root/post-vacation-20261107/P159-FINAL-QUALIFIED-REFS-XML-AND-DEFAULT-PARK-REVIEW01.json)（1,770B／`73747d5b9debb6ed6f9edd76ebfbbd266933588241391974a0bd667b0e2c8c66`）；[Root默认PARK与更早费用](D:/ck3-state/resume91-native-integration/p159-token-range-prod01/ROOT-DEFAULT-PARK-AND-EARLIER-ROOT-COST-OBSERVED01.json)。
