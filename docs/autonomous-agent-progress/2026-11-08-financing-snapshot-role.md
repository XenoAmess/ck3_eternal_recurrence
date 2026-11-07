# P107：融资输入只传已声明角色所需snapshot字段

普通融资的Gap/Emergency及Loan三个SDK消费者有原65536B输入门，但producer此前把完整snapshot中的数MB native history也放入该角色。消费者不读取这些历史，输入却会在typed判断之前拒绝。本单元修复该独立角色的输入正确性；cash/focus及完整Construction链另行验收，不修改任何codec、全局预算、Guard、原件读取或实际动作。

`OrdinaryFinanceCollector` 的public financingGap和真实loanFromCash wrapper现在共用私有copy-present snapshot角色。保留完整frame、actor及alive、gold、逐行war_id、paused/map_ready、PID/gen和hello四个build键；missing、显式null、错误scalar/array/object形状都保原语义，不补默认。expected build键即使null仍优先于fallback键。root、priority、construction ledger、完整cap表、原cash_resources和完整cash_source_frame不裁剪；source extra仍令原Loan source全对象比较拒绝。完整snapshot/history、原Packet与request仍由Java持有，角色不是无损归档或新权威。

两个新增私有helper属于软件结构变化，本次不授运行装载或原地redefine。P100拒绝同链、UNKNOWN、原deadline/账本与冻结工作树均保持。

## 真实来源和模型

原完整history取已qualified Driver1475前139行，仅作为未消费的大扩展加入既有小软件输入，不声称这些行与该FinanceCurrent属于同一实际世界。肯定Loan输入取既有original-producer软件向量 `holyloan/original-v1.jsonl.gz` ordinal314，原件本身明确synthetic-episode/synthetic-cash-source；不是实机Loan许可。完整资源20361B，SHA `4d0b61ac6ce05b16b78b3ff4bf51891b9780ba348edff7d8c8c6da09780c3539`；31项Gap corpus来自g2-research的warcashprovenance/golden.json，68264B，SHA `36133fdf1f0da339cf31f453c7c162a3e909d63ab5b7152adda1d9d1cee0dee3`。

本地模型两次完整源码候选：第一轮缺imports且缺war_id行错误保留parent array，拒收；其后的真实Loan/RawCash依赖补充属后到合同，不计模型遗漏。第二轮字段union部分采用，owner用更小的copy-present/原顺序helper接线，未采用遗漏imports或扩范围实现。两轮均200/stop，TTFT4172.31/2287.28ms，total11324.66/12203.69ms，cached均null；HTTP成功与软件验证分开。原件：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/financing-snapshot-role107/model01`、`model02`。

## 必要软件验收

仅增编Collector1TU，exit0/12class/6.3407652秒，18:58:38.784608Z close。新Test第一次1TU已编，但3方法结果为1P/0F/2E；两个公共接线方法在owner fixture的大写machine ID处构造失败，尚未到Collector。按既有小写regex改fixture，生产Guard不改。只增编该实际修改Test TU并重跑两个error方法，最终2P/0F/0E/0skip，7.1471883秒；首轮31-vector方法绿保留，未重跑，不能写成最终同一JVM3P。

最终覆盖：

- public financingGap→Gap typed Input和Gap result，以及public financingRequest→Emergency的missing/clear/UNKNOWN三态评估，原普通规划command/phase/reason保留。
- public loanFromCash走实际registered软件CASH packet，肯定Projected的planningFrame、observation与encode bytes均对原小输入一致；原Packet/request/cash/source保持。build-null仍CASH_UNQUALIFIED，source extra及浮点queried revision仍FRAME_UNQUALIFIED。
- 原31个Gap向量新做角色对照，28个typed结果相同，3个原拒绝保异常类型/消息；另外覆盖坏top actor不能被fallback洗白、nested actor缺失时maintenance unknown、war非整数/重复/负ID原语义。

本次同输入扩展DATA的完整Gap为3404665B，角色2662B；完整Loan wrapper3406815B，角色4881B。原full仍会撞64K，角色typed成功且原全部对象字节保持。只证明该组件的输入容量/保真行为，不报实机性能或完整Construction恢复。local-service POM新增现有holyloan gzip的精确testResource引用，普通测试可复现且不复制原料；旧测试和codec未重编/重跑。

最终资源关闭为2026-11-07T19:17:46.829631Z（本地11月8日03:17）。原RED、首轮绿和末两case原件分别在 `D:/ck3-state/resume91-native-integration/p107-finance-test01`、`p107-finance-test02`；末JUnit XML42738B，SHA `7429a6488431120ae0b6526c60e1ed784cdd2f09b283f5cd1bb8301aae2e8527`。

下一P108独立减少public cash路径的完整snapshot重复encode/parse，以同一小原件加大history验证所有NormalizedCurrentCash bytes/getters，并实际测量。P109预算角色随后；持续性能目标仍active，本轮新增确认保存日0，10秒目标未达。
