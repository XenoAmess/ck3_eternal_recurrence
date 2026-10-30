# resume90 Java 开发源交付

machine_id: `xenoamess-full-tower-eb9d2c1186`。执行 owner：`/root/java_delivery90`。

本轮用户明确恢复任务、要求 60 并发及自动游玩与八 M 并行，并暂停本地模型服务使用。本岗不发送模型 HTTP、探测或重试；不操作 Game、生产 S 或 MB。开发源提交与当前游戏采用、日期推进分别记录，交付不作为运行岗推进日期的前置。

2026-10-30T14:00Z 后读取 resume89 总交接、source-index 与 `D:/ck3-state/java-delivery-review-20261030/revision66/vacation-handoff/HANDOFF.md`。`D:/r64d` 实际保持 detached `aa4c60e86e`、index 空、恰好四个 Sway dirty 叶；没有 reset、stash 或整树暂存。fetch 读回 `origin/master=84a6b941717c` 后，因无本地未发布提交，切换到该远端提交并原样保留四叶。Native 独立交付岗与本岗各自 index 互斥，并协调普通 push。

默认 `mvn -version` 实测 Maven 3.10.0，Maven home `C:/apache-maven`，Java 21.0.10；这是当前机器的观察，不是生产命令中固定路径。复用 `revision66/build` 与现有 D 盘 m2；新日志、测试输出与本地 Java 执行记录放在 `D:/ck3-state/resume90-java-delivery`。启动的 Sway application `-am -T2` 增编正在进行；最终结果将追加本页。

AGENTS 指定的 `D:/workspace/.codex-task-bus/bin/codex_task_bus.py` 不存在，使用本仓 `tools/codex_task_bus.py` 同协议登记 `ck3-java-delivery90`。这只是协作状态，不新增游戏启动门。

Sway 增编 14:09:24Z 终态：实际 Maven exit0，231.374 秒。其后本地 Java 记录器以 UTF-8 打印混合编码日志失败，外层 exit1；`SWAY90-COMPILE-ACTUAL.txt` 已先保存内层真实 exit0，日志有完整 reactor 成功。只修打印，不重复绿色构建。实际重编 8 模块（wave2-finance、wave2-development、wave3-governance、wave2-planning、wave3-planning、wave3-development、g2-research、application），其余依赖使用已有 classes；不是全图重新编译。

Sway 新 signed 原包类、DirectObservation 与 PublicCodec 三完整类严格 javac0、10P；覆盖六份保留 Native 软件原包、signed/0 身份、public→prepare→decoder→public、错误类型/哨兵及正域 completion/journal 限制。额外既有 InvalidationRead 完整类 2P1F，零 skip：其固定请求游标 0，却循环 `range-command-result.json` 的游标 1 和 `opaque-command-result.json` 的游标 2，既有 decoder 正确拒绝不一致原游标。此生产分支未由本组修改，未放宽 cursor 校验，未将该失败称为通过；固定 query、oracle 参数与期望 sequence 的后续测试修正另列。

最初额外类测试因本地记录器遗漏 `xar.repository.root`、`xar.python`、`jna.tmpdir` 和错误按字符串选择 JNA 版本而逐次失败；均保留原日志，补齐后保留上述真实 2P1F。没有因测试失败重放原生或游戏动作。原件：`D:/ck3-state/resume90-java-delivery/SWAY90-*`。完整软件验收不证明 Native DLL 部署、当前 Game pipe 或游戏日推进。

Root 随后要求本岗直接最小纠正该既有测试：每个 case 按保留原包的 after_sequence 建立请求、Python 原消费者使用同一原游标、断言原包 sequence 1/2/3。仅测试叶变更，没有改生产 cursor 门或原包。严格 javac0/1.840 秒；只重跑此前失败的 InvalidationRead 完整类，3P0F0skip/exit0，8.836 秒。连同前述三个已通过整类，Sway 四类共13P，未重复绿类。
