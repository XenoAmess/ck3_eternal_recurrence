# 宴会 Stage 5 纯价值与预算叶迁移

状态：Java 候选已实现；集中 Maven/JUnit 验收与实际 consumer 接管尚待执行。它不提交 Start，不查询游戏，不写承诺或 ledger，也不授予实机成功。

来源为 `ck3_autonomous_player/src/xar_autoplayer/activity_feast_stage5_value_policy.py` 的 `assess_feast_stage5_start`，原件 SHA-256 `833d2503ef944d8a46516a94fbf3342379c50a32bfef769e9e27463094b2ba0e`。该源没有候选排序逻辑，本次迁移不新增排序或改变策略。

`FeastStage5ValuePolicy` 保留四资源顺序 `gold/treasury/piety/barter_goods`、100000 定点比例、分支优先级、全部 reason/status、条件性收益说明及承诺向量。非负金额和计数使用 `BigInteger`，保留 Python 原整数域，不缩到 signed long 或 double。Gold 只有 configured cost 为正才要求余额、独立现金底线和战争观测；没有战争时不要求战争现金；免费宴会仍需原生可开始、已证明来宾路线和 peaceful spend 许可。`positive_value_supported` 只说明有来源支持的条件性收益，不证明收益实际发生。

`FeastValueCodec` 明确 13 个必填字段，其中来源允许 `None` 的字段必须以 JSON null 表示 unknown；缺字段拒绝。固定四项数组、非负整数、布尔 token、重复/未知字段、尾随 JSON、UTF-8 与 64 KiB 字节边界集中校验。整数拒绝 bool/float/string。旧函数未主动验证 `planning_stage` 的 Python `5.0 == 5` 等意外宽松行为不形成新合同；Java 按用户强类型规范拒绝该类替身，合法整数阶段与全部策略分支保持一致。

唯一直接 production consumer 是 `activity_feast_stage5_start_formal_consumer.assess_feast_start_private_v1`。它在调用本叶前负责 native guest route、同帧 actor/date/revision、资源来源与 commitment 的检查。未来接管端口应在该处构造已验证的 `Request`，进程内调用 Java 叶并显式转换 `Assessment`；不要为每次评估启动新服务。实际 Start 提交、pending/unknown、后态验证及 ledger 继续由既有唯一 authority 拥有，不能从此纯值判断直接提交。

已捕获 38 个**实际未改动 Python producer** 输出，包含原五项测试代表场景、每个拒绝分支、理由优先级、各资源边界、0 Gold/免费路径、Unicode 及 101 位金额。固定 fixture 为 `src/test/resources/feastvalue/producer-golden-v1.json`，59633 B，SHA-256 `ec0f87133decf60ea87898527e2deaa6e1f18c7c9a4b92da538fb16731bd59e9`。捕获机器为 `xenoamess-full-tower-eb9d2c1186`，实际 UTC 时间保存在 fixture 的 `observed_at_utc`；证据工具在 `D:/codex-ck3-demos/2026-10-22-java-phase1/logs/FeastValueGoldenCapture.java`，仅一次性捕获使用，不是默认测试依赖。第一次 shell 引号和第一次 Java 文本块换行调用失败后已修正，只有最终 exit 0 的 38 行捕获作为 fixture。

同机器实际执行旧 `test_activity_feast_stage5_value_policy`：5 项通过、0 failure/0 skipped。Java 默认测试仅读取已提交的固定 fixture，逐行比较实际 JSON 类型域与全部字段，并验证 request 往返；另有缺失/null 区分、错字段、错 token、向量、负数、重复键、尾随内容、UTF-8、尺寸和领域构造器反例。Java 编译/JUnit 尚未在本 lane 运行，由集中构建 owner 执行；上述旧 Python 测试不能代替 Java 验收或真实 consumer 接管。

技术记录按通用存储策略的 record 类于 2027-04-20 复核；固定 golden 是当前候选的可复现输入，变更原合同或正式接管时提前复核。scratch 捕获工具/seed 属可重建过程材料，不永久保留。
