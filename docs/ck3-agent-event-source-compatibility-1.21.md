# CK3 1.21 事件知识源码迁移

此包只迁移游玩智能体事件知识的原版源码分析和实际查询消费者，不迁移 MOD，不授予原生事件操作许可。

基线源码为 `17c38d362fa37aac6f97b4a7c80723a82ba94ff6`。新安装版为 1.21.0 (Florin)、Steam public build 26622941，EXE SHA-256 为 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`。旧版源码只从不可变 1.20.0.4 归档读取，未重写历史资源、历史证明和版本默认值。

## 生产与消费

`SourceCompatibilityReviewCompiler` 读取原 `RegisteredEventKnowledge` 的 198 个键、完整依赖哈希和既有选中定义索引，通过实际文件读取器逐项验证两版源码；定义提取复用 `InteractionSourceBlocks`，词法指纹复用 `EventSourceCatalogue` 的既有 lexer。新 helper 只生成源码 token SHA，不调用依赖 Native option 数的 `catalogue` API，不把脚本 option 当成原生按钮序号。

生产器读取完后重新验证完整 read-set，以规范化 JSON 生成固定资源。资源包含 158 个依赖文件、198 个事件分析项和五个原版事件/GUI 全文哈希，大小 174323 字节，SHA-256 `b685bf37f960f837239de0efa223ef0cf294e5ec18c572747dcc82b0fce965d3`。

| 实际源码结果 | 项数 |
|---|---:|
| 所有既有依赖全文相同 | 10 |
| 选中定义 token 相同，但其它依赖发生变化 | 144 |
| 选中定义 token 变化 | 42 |
| 原知识项无选中源码索引 | 2 |

158 个文件中 43 个全文相同、115 个变化、无文件缺失。154 个定义 token 相同不能证明脚本依赖、GUI、Native 映射或实际效果仍然相同。

现有 `VanillaEventKnowledgeMethods` 的真实公共 decoder → handler → encoder 对明确请求 `ck3_build=1.21.0` 消费该资源。所有行仍返回 `status=unavailable`、`contract=null`、`observations=null`；`analysis` 标记 `source_only`、`native_binding_status=unqualified`、`material_effects_verified=false`。即使全部依赖相同也没有例外。未登记键无源码分析。旧版本、旧默认值、原完整知识目录、原 EXE 白名单和 Native provider 许可不变。

实际启动链 `EventSourceReadContext → EventRuntimeInstaller.install → TrustedEventSourceContext.open` 改为从真实五份 stock 文件选择固定的已审源码版本，并在后续校验中继续使用该版本。1.21 的源码上下文可以建立，但 `requireBuild` 仍拒绝其 Native 操作；旧 `.4` Native 帧也不能借用 1.21 源码。`openEvidence` 的根/声明功能不产生源码版本许可。

## 验证与真实边界

独立 Java 21 编译验证了五个生产 TU。12 个独立用例分两相通过：首相 10P/0F/2E，两个错误均在新 MCP 测试的描述符 fixture 缺失 `inputSchema.type` 时被原构造器拒绝；只修 fixture 后，两例重新编译并取得 2P。原失败保留，没有宣称单相 12P。

验证覆盖了真实 Java 生产器从归档和实际安装源码重现资源 SHA、198 行实际公共查询、原完整旧版查询逐行结果、旧默认值与错误参数、原大响应分支、严格 schema/类型/依赖/分类检查、源码选择后的变更拒绝，以及新旧源码不能跨借 Native 证明。安装源码集成测试是显式选择的 `SourceCompatibilityInstalledSourcesIT`，必须提供真实 `xar.source.baseline` 和 `xar.source.target`；普通 CI 不自动运行该 IT，缺参不能计作跳过成功。

本包没有运行旧独立 Python 全量 producer 回归，没有声称整个 SDK/冷暖启动、Native、Game、OODA 或动作验收通过。未接管旧 file 决策消费者，没有模型 HTTP，没有更改正在运行的 M1 类、用户 profile、存档或 MOD。

## 下一项实际 Native 输入

优先迁移 `query-current-event-window-v1` 的 exact-build、同帧暂停状态、实例身份、定义 key、calculated/runtime ordinal、可见/可用选项及 source/native option 映射。随后迁移真实 letter root、scope 原生类型和关联身份；最后以原 action ACK、同实例窗口消失及后置效果闭环。旧 `.4` root/idle/manager 地址和 raw scope 类型不得因本包的源码标签变化而放行。

其它仍硬绑 `.4` 的 Sway、FamilyEducation、Gift、Mercenary、WarPayment、Prisoner 观测消费者继续拒绝未资格的新 Native 数据，不能全局替换版本字符串。新 1.21 实际字段及动作来源由 Native/Runtime 的真实资格分别补齐。
