# open_kaishek

`open_kaishek` 是一项已批准立项、正在进行 Phase 0/早期实现的开源 JVM 子项目。

它的目标不是重写 CK3，而是提供一条可以独立运行的 Paradox 脚本工具链：从逐字节保真的解析开始，经过版本与目录感知的静态验证、严格 IR 编译和白名单语义执行，最终在有限世界快照上运行“半套仿 CK3 Runtime”，并用真实 CK3 与 MCP 差分结果认证每一项可执行语义。

## 已确定的技术约束

- 实现语言与运行平台：Java/JVM。
- 服务与集成框架：Quarkus。
- Parser、validator、IR 和 Runtime Kernel 必须保持纯 Java、无 Quarkus 依赖。
- Quarkus 只负责服务入口、配置、依赖装配、缓存和外部适配。
- 第一优先 profile 是 CK3 1.19.0.6 与 `mod_zhongguo_style` 的 361 机制。
- 未认证语义必须明确返回 `UNSUPPORTED`，禁止猜测、宽松吞错或静默 no-op。
- CK3 实机仍是版本绑定语义和正式发布验收的最终权威。

## 当前状态（2026-09-01）

项目所有者已授权进入 Phase 0。当前提交包含可离线构建的纯 Java 基线：lossless
parser/CST、profile API 与 CK3 1.19.0.6 profile、schema validator、strict IR
合同、finite runtime 原语、差分 snapshot/trace 合同、361 domain schema，以及不启动
Quarkus 的 CLI。另有一条明确标注为 synthetic 的 014 纵向夹具走通 Parser → Validator
→ IR → VM。M0 仍待正式评审，因此这些结果标为 `static-ready`，不是 CK3 实机能力。

- Parser：目标 corpus 的 27 个 `.txt/.gui` 文件逐字节 round-trip 通过（2,677,440 bytes，0 diagnostics）。
- Validator/IR/Runtime：提供最小、fail-closed 的合同与单元测试；synthetic 014 夹具执行
  `delivered → appeal_open → closed`，完整 361 业务仍未形成闭环。
- CK3/MCP：exact-build 身份已记录，但没有 paused live artifact；`fixture-live`、`differential-certified` 与 `product-live` 均不可宣称。
- Quarkus：仅保留集成壳，依赖按路线图延后；没有复制第三方源码。

## 文档入口

- [项目立项报告](docs/project-charter.md)
- [目标架构与“半套 Runtime”边界](docs/architecture-plan.md)
- [阶段计划与里程碑](docs/roadmap.md)
- [验收与 CK3 MCP 差分策略](docs/acceptance-and-differential-testing.md)
- [参考仓库与计划复用目标](docs/reference-repositories.md)
- [ADR-0001：Java/JVM、Quarkus 与核心边界](docs/decisions/0001-java-jvm-quarkus.md)
- [ADR-0002：Phase 0（M0）开工与冻结门槛](docs/decisions/0002-phase0-start.md)
- [Phase 0 验证记录](docs/phase0-verification.md)

## Readiness 边界

`static-ready` 只表示源码、合同和离线验证可复核；它不等于 CK3 加载、Runtime
等价或 MCP 认证。任何未知 opcode、版本不匹配、缺失字段或未认证随机/调度语义都必须
显式返回 `UNSUPPORTED`。synthetic 014 仅证明有限离线夹具；后续 M3/M4/M5 仍需扩展
真实业务范围或取得 paused CK3 artifact 才能推进。

## 项目口号

> 离线穷举我们真正拥有的业务语义，实机只验证 CK3 真正拥有的引擎语义。
