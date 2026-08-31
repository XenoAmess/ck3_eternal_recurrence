# open_kaishek

`open_kaishek` 是一项已批准立项、尚未进入实现阶段的开源 JVM 子项目。

它的目标不是重写 CK3，而是提供一条可以独立运行的 Paradox 脚本工具链：从逐字节保真的解析开始，经过版本与目录感知的静态验证、严格 IR 编译和白名单语义执行，最终在有限世界快照上运行“半套仿 CK3 Runtime”，并用真实 CK3 与 MCP 差分结果认证每一项可执行语义。

## 已确定的技术约束

- 实现语言与运行平台：Java/JVM。
- 服务与集成框架：Quarkus。
- Parser、validator、IR 和 Runtime Kernel 必须保持纯 Java、无 Quarkus 依赖。
- Quarkus 只负责服务入口、配置、依赖装配、缓存和外部适配。
- 第一优先 profile 是 CK3 1.19.0.6 与 `mod_zhongguo_style` 的 361 机制。
- 未认证语义必须明确返回 `UNSUPPORTED`，禁止猜测、宽松吞错或静默 no-op。
- CK3 实机仍是版本绑定语义和正式发布验收的最终权威。

## 当前状态

截至 2026-08-31，本目录处于 **立项文档阶段**：

- 已有项目章程、目标架构、阶段计划、验收方案和参考仓库账本。
- 尚未创建源码、构建脚本、Quarkus 工程、测试工程或发布流水线。
- 尚未选定或复制任何外部仓库代码。
- 正式实现必须从路线图的 Phase 0 合同冻结开始。

## 文档入口

- [项目立项报告](docs/project-charter.md)
- [目标架构与“半套 Runtime”边界](docs/architecture-plan.md)
- [阶段计划与里程碑](docs/roadmap.md)
- [验收与 CK3 MCP 差分策略](docs/acceptance-and-differential-testing.md)
- [参考仓库与计划复用目标](docs/reference-repositories.md)
- [ADR-0001：Java/JVM、Quarkus 与核心边界](docs/decisions/0001-java-jvm-quarkus.md)

## 项目口号

> 离线穷举我们真正拥有的业务语义，实机只验证 CK3 真正拥有的引擎语义。
