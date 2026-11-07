# 普通恢复附件准备中的同调用编码复用

机器：`xenoamess-full-tower-eb9d2c1186`。本单元只减少普通恢复附件准备中的一次纯序列化；没有诊断原UNKNOWN、改变当前head47准入、执行Root/SavedLive或触碰Game。

`SavedAttachmentSourceStore.prepareMaterial`原先先比较`saved.encode()`与`material.savedDriver().encode()`；首比较相同时，再将第二次`saved.encode()`与固定严格物理重读所得Driver的编码比较。同一局部不可变saved操作数在成功路径上被编码两次。

候选只在原方法体内暂存首次固定编码。actor必须是标准`BigInteger`且字节不超过8MiB，才在本次第二比较中复用；首次比较之后，非标准数值或过大结果的引用立即清空，走原第二次编码。material Driver与物理重读Driver这两个不同的比较操作数仍各自真实编码，第二次物理读取及verify/hash/ACK不省略。只计两处显式saved操作数，成功合格路径从两次编码降为一次；不是全部表达式编码数2→1。首次比较失败或抛错时，不进入后续物理读取。没有新方法、类型、字段、全局或ThreadLocal缓存；局部字节不能跨调用、material或frame流转。

## 模型候选与接管

共享caller按完整相关源码进行了两轮真实普通HTTP源码请求，均完整200/stop/DONE、JSON有效，但语义拒收：首轮为检查长度另调encoder，再次编码赋值；第二轮为fallback提前计算两个操作数，既多编码也破坏原短路顺序。owner保留两份原件，修正方法体，没有第三次请求。HTTP成功未计作候选实现成功。

首轮TTFT4416.8844ms、总9828.5504ms，28731输入/683输出tokens；第二轮TTFT1243.1587ms、总5715.6085ms，28939/697tokens。两轮cached tokens均未报告，不从耗时差推断缓存命中。

原件前缀：`D:/ck3-state/resume91-java-delivery/ordinary-p0-20261105/restore-attachment-encoding-reuse103/`。`model01`、`model02`各保留实际REQUEST、完整CONTENT与RESULT；共享能力案例由Models唯一writer另行发表，不修改活跃caller或Runtime配置。

## 验证与实际采用边界

候选采用固定encoder、原错误消息及原物理调用顺序。必要类型验收只编本次一个生产TU，复用既有已合格依赖；不为局部字节变量扩测试API、替换encoder、构造私有许可或执行旧绿色用例。旧source01仅产生未执行配置；在编译BEGIN之前发现大数组引用生命期可以更明确后，owner补充立即清理，形成最终source02。旧稿没有运行编译，不记软件RED或最终资格。

最终生产源52749 B，SHA-256 `9b9040bdd539cd31e3cf5968b877b01b705167af4eb340bb5517cd0a385c78b3`。Native唯一1TU编译实际exit0 / 9个原有class，4.7081031秒，无超时，contract=true；`2026-11-07T07:56:08.682196Z`资源关闭，held=false、资源槽全部null。0新Test TU、0测试RUN、0旧绿重跑。Root独立读取原ACTUAL和关闭回执；这次必要类型验收不授实际Root/SavedLive执行或游戏能力。

原资格目录：`D:/ck3-state/resume91-native-integration/p103-attachment-encoding02/actual/prod/`，`ACTUAL.json`与`MANAGED-CLOSE.json`分别保留真实退出、完整进程墙钟与资源释放。源码仅修改[原方法体中的局部变量](../../java/ck3-control/application/src/main/java/org/xar/ck3/control/application/checkpoint/SavedAttachmentSourceStore.java)，parser/encoder与依赖没有重编。

薄资格：`D:/ck3-state/resume91-native-integration/p103-attachment-encoding02/QUALIFIED02-ONE-SOURCE-TYPING-ONLY.json`，4649 B，SHA-256 `9b9f6681329a6431ed596f0dfab57c817941bd1b0db1fcea8b2e0964678bd102`。其中保留旧candidate01未执行、最终源及各实际phase回执，不把类型资格扩成实机验收。

当前单元只针对普通恢复附件准备路线，未证明普通OBS/PLAN热点或冷恢复完整墙钟改善。源码、软件资格、正式发表与实际装载分开；本轮无新增确认保存日，不授10秒目标通过。
