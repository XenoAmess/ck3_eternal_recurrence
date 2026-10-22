# 宣战目标研究顺序：Java 迁移边界

本包迁移原 `declaration_objective_priority_v1.py` 的纯 0/1 producer，并提供其唯一生产消费者 `strategy._preferred_native_declaration` 的等价纯排序函数。该函数只回答下一个研究目标的原始输入下标；不授予宣战、胜率、收益、领土转移或动作执行资格。模块没有 Game、RPC、HTTP、文件、账本或 writer 操作。

原始调用链为原生 declaration 观测行 → 同帧战力评估过滤 → `_preferred_native_declaration` → 后续独立的合法性和完整兵力准入。原 leaf 的唯一生产消费者是 `strategy.py:556–631`；单元测试另直接调用 leaf。消费者只有在没有目标级原生战力评估时才使用 0/1 优先级，且它位于 evidence rank 与六项 power keys 之后。已评估目标始终保留旧顺序；负网络贡献只在比较 lane 上截为零，原输入不变。最后仍使用 CB rank、title count、target ID、CB index、configuration index；所有完全相等的键保留输入第一行。

`DeclarationObjectivePriority.priority(LeafInput)` 对来源严格为 `native`、CB 严格为 `claim_cb`、claimant 精确等于正 actor、非空且全部为正整数的 title IDs 返回 `ACTOR_OWNED_NATIVE_TITLE_CLAIM(0)`；其余已表达或未观测情况返回 `OTHER_OR_UNOBSERVED(1)`。`reclaim_relic_artifact_war` 和未知含 claim 的 CB 不因此获得玩家领地收益。缺少 title IDs 也不证明没有其他领土、政治或神器后果。

`preferredIndex(SelectionInput)` 复现原消费者，返回原列表下标，空列表为 `OptionalInt.empty()`。调用方必须继续执行原来的同帧/来源/完整性检查，不能把任意 `PowerAssessment` 当作新鲜原生观测。原生证据完整性和来源 SHA 的验证属于原 producer/adapter，字段 `source=native` 本身不能认证来源。此包不改变这些资格。原始政策所依赖的 exact-build 原版定义与 SHA 保留在 Python producer docstring 中，golden 绑定其完整源码。

`DeclarationPriorityCodec` 是显式投影边界：leaf schema 为 `xar.ck3.declaration-objective-priority.input/v1`，排序 schema 为 `xar.ck3.declaration-objective-order.input/v1`。actor 必填且允许 null；leaf 的 declaration 必填且允许 null；排序 declarations 必须为数组。rich legacy 行只投影本包列出的八个字段，power 行只投影本消费者读取的七个字段，不能直接宽松反序列化整个旧容器。未知字段、重复字段、缺少 envelope 必填字段、错误类型、非法 UTF-8、尾随 JSON 均拒绝。旧 Python 对若干错误类型返回 1；Java wire 对这些不合法合同显式拒绝，这不是把 malformed 候选升级为合法输入或改变正常策略。golden 分别记录正常差分与这种边界拒绝。

`JsonField` 保留 missing/null/value，title IDs 的空数组独立存在。负 ID、零 ID、空字符串均保留为真实输入，只是不获得 own claim 优先级。全部整数使用 `BigInteger`，保持 Python 整数域，不经浮点或 `long` 中转；因此即使两个 128 位 risk 值只相差 1，也保留顺序。这是 Python/Java 内部数值通道，不能经 JavaScript Number 转发。JSON 使用共享 `StrictJson` 的 64 KiB 单包、UTF-8、精确整数与 canonical 规则，不另创宽松编码器。

固定资源 `src/test/resources/declarationpriority/original-producer-golden.json` 由显式 Java capture 工具运行**原 producer、原完整排序 consumer 和原 7 个单元测试**采集，并绑定源码/夹具字节数与 SHA。八个历史原生目标只证明当时观测子集，不代表完整候选集或当前游戏状态。额外样本检验 missing/null/empty、source/CB 大小写、玩家与他人 claimant、稳定平手、六项 power precedence、超 64 位精度、负网络贡献、严格 wire 拒错和序列化往返。默认 JUnit 只读取已提交资源，不调用 Python，也不依赖未跟踪 Python 草稿。java06 曾实际出现拒错夹具 RED：测试将解析后的 DecimalNode 重新输出，令原 `31254.0` token 变成 `31254`，未把原错误类型送入生产入口。修复只在捕获/测试路径保留 `raw_request_json` 字符串并直接送生产 decoder，额外直接字面测试覆盖 `.0`、指数形式和 title/claimant 浮点；生产整数检查未放宽。原 java06 与首次 golden 保留在外部日志/构建证据中。

捕获命令由既有默认 Java 21 执行 `CaptureDeclarationPriorityGolden.java`，参数是仓库根、现存 Python 解释器和**不存在的**输出路径；原记录不覆盖。首次实际捕获绑定 `machine_id: xenoamess-full-tower-eb9d2c1186`，时间和精确源码来源见 golden。原 7 tests 实际 PASS、0 skipped。Java 编译和 JUnit 由 Root/M7 的集中完整 reactor 验收，本文不把尚未执行的 Java 检查写成通过。

生产接管入口：同一受管 Quarkus 宿主按批接收已认证观测投影，直接调用本纯 Java API，再把原下标映射回原始行；不为本叶创建新服务或每候选一个 HTTP。`strategy.py:15436` 的首次选择须传现有同帧 assessments；`strategy.py:15543` 的 alternative 选择只传原先过滤后的 unassessed 子集。两处都映射回各自的原列表，保留其后 int32 query target、available steps、已拒绝目标与完整 force admission 分支。正式切换须同步原 producer→strategy 消费者→后续正常合法性/完整兵力准入闭环，并执行同帧已评估 fallback 和真实 postcondition 回归；接管完成前不得称为 live migrated。本交付没有修改旧 Python、冻结 runtime/SDK 或真实玩法策略。
