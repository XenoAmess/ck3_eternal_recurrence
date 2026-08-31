# ADR-0001：Java/JVM、Quarkus 与核心框架边界

## 状态

已接受，2026-08-31。

## 背景

项目需要一套可独立运行、适合长期维护和 CI 批处理的 Paradox parser、validator、执行器及有限 CK3 Runtime。用户已明确指定 Java/JVM + Quarkus。同时，现有优秀参考项目分布在 Kotlin/IntelliJ、F#/.NET、Java 和 Rust/Wasm 生态，必须避免因借鉴某个项目而把核心绑定到其 IDE 或服务框架。

## 决策

1. 项目核心使用 Java/JVM。
2. Quarkus 是服务与集成框架，不是 parser/runtime 的基础设施。
3. Syntax、profile API、validator、IR、runtime kernel 和 differential contracts 均为纯 Java 模块。
4. CLI 是 CI 和本地批处理的首要入口，不要求 Quarkus 启动。
5. Quarkus 层负责配置、依赖装配、REST、缓存、健康状态、指标和 MCP orchestration。
6. Windows named pipe、CK3 进程和 MCP 接入属于 adapter，不进入核心模型。
7. Java、Quarkus、构建工具和测试框架的精确版本在 Phase 0 根据当时支持矩阵固定；立项文档不追随“最新版”。

## 理由

- Java/JVM 适合构建强类型、长期维护、可嵌入和高覆盖测试的 parser/runtime。
- Quarkus 能提供清晰的服务边界和集成能力，但其启动生命周期不应污染毫秒级 parser/runtime 单测。
- 纯 Java 核心方便 CLI、Quarkus、测试和其他宿主共享，也便于未来对不同 Paradox profile 复用。
- 该边界允许借鉴 Chronicle 的 Kotlin/JVM 语法经验，同时避免引入完整 IntelliJ PSI 运行时。

## 结果

正面结果：

- 核心可在普通 JVM 测试中快速运行。
- Quarkus 服务可以独立替换或升级。
- 依赖方向清晰，方便开源用户嵌入。
- CK3/MCP 专有集成不会污染通用 parser。

代价：

- 需要显式维护 core DTO 与服务 DTO 的边界。
- 不能直接复用 Chronicle 的 PSI 树作为核心 AST。
- Quarkus 的部分便利能力不会下沉到 runtime kernel。
- 模块化和合同设计会增加 Phase 0 工作量。

## 被否决的方案

- **以完整 IntelliJ 插件作为 headless 核心**：可运行但过重，PSI/Project/VFS/index/extension point 耦合不适合轻量 CI Runtime。
- **直接把 PDXTools 当作 CK3 Runtime**：Java 外形合适，但执行层面向 Stellaris且 CK3 世界语义缺失。
- **Quarkus-first 单体应用**：会让 parser/runtime 测试、嵌入和复用依赖服务启动。
- **完整重写 CK3**：范围失控，且仍无法取代专有原生引擎与实机验证。
- **只做 parser 不做 Runtime**：不能满足已经确认的项目目标，但 parser/validator 仍作为可独立止损成果保留。

## 复审条件

- Quarkus 无法支持计划中的服务/CLI组合，且维护成本显著高于收益。
- 核心出现无法避免的框架反向依赖。
- JVM 性能经过真实 corpus benchmark 证明无法满足目标，而不是仅凭预判。
- 项目目标或用户技术栈要求发生明确变化。
