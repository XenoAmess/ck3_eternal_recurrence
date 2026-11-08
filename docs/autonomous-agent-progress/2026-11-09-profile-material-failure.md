# P152：完整软件采样在 MATERIAL 断言失败，未启动解码

本次唯一 current350／compiledTest15 publicApplied workload 实际失败：1F0E0skip，child exit1、非timeout，资源已真实释放。后继source-mode utility未BEGIN、编译／解码0次；不能把JFR文件存在或header完整称为采样资格通过。原失败、raw、实际剩余repository、完整fixture、stdout／stderr／XML均未移动删除，不据JDK dump／chunk release外推所有历史临时chunk永久保留；没有自动重试、重录或补解码。

实际执行的是compiled15完整10类，基源码37,883B／SHA256 `8156161471931b76c87fb7e8f16ebbff8d90f9c0ec06ba4c9ec98a0d3fa0f516`，不是当前formal measurement版或compiled16。唯一方法 `ConstructionFullProduction113Test#fullFuturePlanRunsActualIntentEffectColdVerifierAndFullMaterialPublication` case148.641秒，Jupiter suite148.678秒；console的148944ms是整JUnit run，三者不混。没有业务生产、Test、Main、SDK或工具的额外编译。

失败为旧Test181的 `assertInstanceOf(MaterialAvailable, productionCollector.material(...))` 实际返回 `MaterialMissing`。之前resolveCommand、真实软件history publication、cold verifier、synchronizeOutcome和applied断言已经走过，MATERIAL publish183未到。该类型断言没有打印返回record的reason，不能由失败类型反推唯一原因。

## 原件确定了什么

Test177-179新建MATERIAL请求，但仍传入原command.deadline `2026-11-08T17:48:04.234530600Z`。最后三次真实软件READ的Native ACK原件均为native_ok=true且在此deadline前：

| READ | request_id | response_received UTC |
|---|---|---|
| ROOT | step-11-ab01fa0be65d | 17:47:44.162245100 |
| CASH | step-12-c56d73599d17 | 17:47:51.478701400 |
| CONSTRUCTION | step-13-92d713db34c5 | 17:47:58.821298 |

CONSTRUCTION原始command_result也为ok／accepted／source_available；不能说它从未发送或ACK迟到。其planning-read归档存在，最后文件mtime为17:48:06.673225，XML收尾timestamp17:48:07；mtime只是可用文件属性，不是精确分支或方法返回时钟。旧deadline复用因此是具体hazard，但仍不是已记录的MaterialMissing.reason。

实际Collector.material有两类Missing出口：CONSTRUCTION非Known时的通用missing；以及捕获IllegalArgumentException后带message的missing。Changed另返回MaterialFrameChanged。当前Test observing wrapper会打印返回Unavailable的operation／reason，原stdout和XML未出现该行；Known后fresh ending／finalizer等校验属于候选，仍不能只凭ACK和归档存在确定Java最终包装结果或异常。精确reason、deadline是否为本次唯一根因、P150或Guard的因果均为UNKNOWN，不据此改生产或放宽任何校验。

## 费用、预算与未解码范围

完整controller154.6762895秒，workload recorder actor153.4277196秒，workload outer154.466808秒；actor含父BEGIN／POST验证，不是纯child wall。同retained OS birth的child lifetime152.8974934秒、process CPU88.984375秒另记。独立observer线程CPU16.6875秒／scan elapsed27.5806511秒／最大gap369.3928ms，不能隐藏、相减成应用CPU或当成A/B收益。child stdout2012B／stderr7891B原件完整，未把outer空输出当child0B。

最早已知Native合同17:18:39.471059Z→CLOSE1769.229225秒／原资格1970.148092秒／费用tail2036.855033秒；包含工具D草稿、source审阅、配置准备、等待、JFR失败workload和后处理。较窄首次artifact17:40:38.418981Z起450.281303／651.200170秒不替代此窗；更早Root合同／source准备仍UNKNOWN，不记0。0新增确认保存日，不计算有限秒／保存日。

原raw9,493,167B／SHA256 `6784a2d9ad2ae20f8f823a28e5586efb8f0dd46722c23dafd7ec8cf7bee878a9`，只核到finished chunk extent header。事件EOF、实际settings、DataLoss、截断／样本分区和P152新增callsite轴全部UNKNOWN／UNDECODED；新工具未编译或执行，不能提供本次CPU归因。afterclose逻辑snapshot metadata1,219,785B，后续资格／费用tail另保；运行时观察非硬瞬时峰值，尾部连续覆盖未知。未扩大raw／repo／derived／metadata预算或移动原件求通过。

P150保持限定组件的软件采用及当前350 class graph，不外推为此次whole fixture通过，也没有擅自rollback；P149负结果、P151只读PARK和P141历史预算失败不改写。后到P153在另单元、无JFR的新fixture唯一诊断1P、case128.708秒，lazy failure未触发、没有reason输出；未刷新原command deadline／原120秒或重用本fixture，不将该PASS回填成本次通过，也不是A/B性能或P150因果证明。P153Test仅D、未正式采用，[诊断资格](D:/ck3-state/resume91-native-integration/p153-material-reason-test01/QUALIFIED-P153-SINGLE-CASE-DIAGNOSTIC-NOT-REPRODUCED01.json)原件独立保留。本次只发表三份事实文档，无D utility／P153Test源码采用或发表附带的新执行，无Runtime／Game／P100／head47／SAVE或10秒目标信用。

原件：[Native失败资格](D:/ck3-state/resume91-native-integration/p152-current-applied-profile01/QUALIFIED-P152-FAILED-WORKLOAD-NO-UTILITY01.json)（9,550B，`052ed704b327b4a19ec07c5fee406ca83f1f91e20da409a28b400c6a00e08b32`）；[原XML](D:/ck3-state/resume91-native-integration/p152-current-applied-profile01/reports-workload/TEST-junit-jupiter.xml)；[费用与更早锚](D:/ck3-state/resume91-native-integration/p152-current-applied-profile01/FAILED-WORKLOAD-EARLIER-KNOWN-COST-TAIL01.json)；[compiled15精确入口](D:/ck3-state/resume91-native-integration/p152-current-applied-profile01/EXACT-XML-FAILURE-AND-COMPILED15-SOURCE-ENTRY01.json)；[owner只读定位](D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/construction-callsite152/read-only-failure01/REPORT.json)（6,127B，`9bcf612a0d657636d216080f85c3cebdb58a7ab11162b9e19b1bec7160701e6b`）。
