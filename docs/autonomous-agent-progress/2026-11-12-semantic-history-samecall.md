# 语义回放复用同调用独立重建的历史行

已闭30秒JFR的业务Execution样本显示 FullJsonTree.read 热点，其中 NativeSemanticEvidenceVerifier 的 canonical 验证先用原 Driver／原 Native／manifest 完整重建 SEM，Assembler已解析各原 history row，之后 verifier 又逐行解析相同原件。本单元只复用这一调用内已独立重建的行；采样是定位证据，不是 CPU 秒数或性能收益证明。

私有 requireCanonicalProjection 仍按原顺序读取／核 hash／重建／校验完整 identity、原 Driver、source、stamp 和 SEM。只有 facts.driver 与本次原解码 Driver 是同一个对象，才返回 rebuilt Complete 自有的 immutable history List。比较的 consumer SEM 不作自己的 oracle。不同 Driver／wide-material fallback 与 legacy 分支仍走原逐行 parser；size／行序／equals／原错误文本、slot、head 和 archive callback 的顺序不变。无跨调用或跨轮缓存，没有公开 trusted AST 入口。

初稿58私 record 已有实际单TU／3类和完整两项通过；因 attempt46 既有新增嵌套类型不可见的真实装载边界，owner将私返回值机械改为 List，producer内同对象资格仍保。旧稿、原回执保留；最终59独立增编单TU／2类，只有原 Top 与 ArtifactReader，未发行新类型。正式 NativeBodyStage／原包解析与 close 路径按已有差异机械保留，没有以 active 全叶覆盖。

实际59和正式59分别必要增编1TU／2类，并分别复用原冻结 SemanticDriverReuse366Test12620B／`23671edcf9724d6c2fcad270054a616e7258ac522f1649380bf93fd71832a896` 三个产物类运行完整两项，各首次2P／0F／0E／0skip、输入不变、CLOSE释放。真实覆盖 profile3／4 的 typed 同 Driver 与 wide 不同 Driver fallback、distinct原件读、later callback修改借用数组、IO异常同对象、head漂移和坏manifest。没有改测试或用 parse 计数镜像。仓库已有更大的三项历史类及外部旧源性能用例，本次未改，也不宣称已执行其第三项。

正式编译ACTUAL1632B／`e8e9b14e2cd86039736992f7194939e9f2f6001dab51de3aad0e424da84950c5`；正式whole2 ACTUAL1436B／`4b8a6b4ccce2d16e02991e9705914d79d4d1ed4c0a4b2f3529e95ca8633ef2be`、CLOSE204B／`afed177519c7bc9ed06becfa6588e1b7ab91fee3e730a10e0e1793cf33c7732e`。原件在 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01/semantic-history59-{compile01,junit01,formal-compile01,formal-junit01}。机器 xenoamess-full-tower-eb9d2c1186，2026-11-12。

本地模型按 owner 给出的私有同调用合同实现四处生产 edit；owner补外层类型 import，并作去 record 的等价部署适配。首次模型 NO 的错误源码理由已被真实 Assembler 行解析否证，不用它封案。软件／正式发表与运行装载、真实墙钟及新增 SAVE 分别记账，本单元不授实际提速或10秒目标。
