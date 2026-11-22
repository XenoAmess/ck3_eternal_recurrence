# R0065：通知标题可见，完整送达仍未通过

2026-11-22，machine_id: 4-8e1c2f1861，CK3 1.21.0／build26622941。scene20261122b／R0065的登记来源及Q48编译来源为 `e11ad8dff03b124c27ea0f76fd5bd5b3e3ca149f`；闭场后两处effect→text修改不倒算为本场已加载或已验证。

本场正常继续R64终档，保留两份独立物理SAVE，raw53151360→53151432，新增3自然日。基线23,514条完整记录及选中globals／news冷载比较相同；终点有真实自然差异，原完整比较、Raw、whole和归档引用均保留，不要求跨日全图不变。

## 六份原DTO的实际边界

每个原advance_day(1)后立即执行两次只读toast query，没有强制发行、宣传、事件或额外查询。

| 自然日 | 原始日期raw | 两次原DTO | 可授与缺失 |
| --- | --- | --- | --- |
| 1 | 53151384 | empty／empty，queue0 | 没有观察到通知 |
| 2 | 53151408 | visible_pending_frame→visible，queue1 | 标题“新币进入市场”确实渲染；description为空，两类saved scopes为空，recipient与news-origin均不可用 |
| 3 | 53151432 | visible_pending_frame→visible，queue1 | 同样保留可见标题；相同缺失仍在，delivery_confirmed仍false |

因此不能把结果写成“什么都没出现”，也不能只凭中文标题猜localization key、币／新闻身份或接收人。本场合格本地送达仍为NOT_OBSERVED；全游戏／所有玩家送达更未通过。通知正文及来源／接收人关联是当前P0，后继修复仍须真实软件和实机证据。

## 正常闭场不改变PARTIAL

两条保存读回pipeline原操作都退出0；终点差异按原比较政策保留。公共run原0／1583.2730918秒，verify原2／1.1142701秒，整案PARTIAL、case与qualified boundary均false。Game18364、Host、Job、keeper均实际0，CAS16093→16094、done/resources[]。原closure的通用note仍有旧run／verify2句式，原件保持；实际运行结果以typed字段及原wait的run0／verify2为准。

Q48原操作0／75.7663059秒、公开consumer PASS，v23配置238 flags／862 TU图；实际2条CXX、3条link，22个正式fixture精确依赖复用／0新增，curated OFF新增一次实际0，XQOL OFF沿Q47精确复用。它不授foreign267 ON能力，也不能补通知送达；862不是本次重编数。

闭场后只采用两个现有news脚本各一行effect→text类型修复，未采用候选里的新增mirror测试。既有BuildContractTest 8项与WorldNewsJournalTest 6项共14个distinct检查实际全过，原操作0／28.8759822秒；日志为main无重编、test源52个重编，复用现有target。它们只授静态／source软件范围，无新版引擎正文或来源关联正例；旧634金融／453共享结果保留原源范围，不外推本修复。Generic把rendered text硬比raw key的独立consumer候选另行处理，不预授资格。

期货GUI业务有限累计6/6及历史35次AI付费发行、4个无地阳性保持原范围，不在本场重计。正额资金费实机、逐日金融覆盖、长期容量／性能、完整Mod及Workshop首发继续待验；旧失败、PARTIAL、UNKNOWN与日期缺口不改写。

[六DTO、两SAVE、原run／verify／闭场及Q48精确pins](../../docs/maintenance/evidence/2026-11-22-financial-markets-r0065-notification-partial.json)。本文仅消费已完成的小元数据；未重读.ck3、audit或Raw正文，未执行Game、OS、Git或编测。
