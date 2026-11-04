# 同次回放复用原始 Native 包的已解析输入

`DriverObservationEvidenceReader` 已严格解析原包的 envelope，随后 assembler 的首个投影又从相同 framed bytes 解析该 envelope。本单元仅让 Reader 私有构造的输入携带原 bytes 与解析结果，交给同一次 assembler 调用；实际 framed bytes 必须精确匹配，任何不匹配仍走原严格解析路径。state 仍独立解析并与包内 state 全量比较，原 framing、长度、SHA、session、snapshot、revision、semantic guards 与完整构造器不变。消费后在 `finally` 清除临时输入，不跨调用保留验证结论、Head 或 Complete。

原始实际变体已完成必要软件链：2 个生产 TU 首编生成9类，6.8365938秒；新 Test 1TU生成2类，4.7603837秒；两个新 DATA 方法2P，3.8740265秒。另将原 A 的3个已编译方法仅 RUN，3P，3.8903155秒。所有 phase 各自 terminal、post、fence、close 完整且释放；没有重编旧 A、Support，未重跑旧309。两份 XML 为 `92a52b36…`／`c5fc02e5…`，无 error、failure、skip 或 abort；不同 phase 的预算不可合并宣称为一个 TOTAL。

正式源码只精确投影这两叶的 owned spans。正式 Reader 原有五参 decode/archive 接口、Assembler 及类说明的额外当前内容完整保留，全部 outside 可逆回原正式前像。该正式组合尚未单独编测，不能把原始实际变体的2P＋3P授给组合整体。新 Test 原样采用 owner 最终源 `019fe1d5…`；生产原变体为 `b28cec90…`／`0ad854fa…`，正式组合及完整来源见[索引](../maintenance/2026-11-05-native-packet-input-sources.json)。

生产模型首派 length，全文未读整弃、0代码采用且无R2；生产由 owner 接管。测试只部分机械复用既有合法 scaffold，其新增逻辑及修正由 owner 完成，完整分账保留在 M6 原件中。源码、软件通过、正式发表、实际装载及速度分开记录。

本单元引入新的实现类型，不具 body redefine 资格，也未证明当前 Quarkus 实例可加载这些新类型。当前健康普通游玩不为它重载；没有 Runtime 采用、实机收益、自然 M6 或新 V4 场景资格。当前45秒样本是另一普通 postappend／cycle／read-completion 窗口，不能用本单元的软件通过解释该窗口的实际耗时。首负 ACK 通知的必要新测试与 Runtime 正常运行继续优先。
