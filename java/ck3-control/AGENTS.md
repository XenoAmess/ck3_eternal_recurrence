# CK3 Java 控制服务

- 新生产入口使用 Java 与 Maven，Quarkus 承载业务，纯领域与构建支持保留单独模块边界。[Java 架构](../../docs/java-next-generation-architecture-2026-10-22.md)和[迁移计划](../../docs/python-java-incremental-migration-plan-2026-10-22.md)给出生产接管顺序。阶段状态见[版本迁移记录](../../docs/ck3-1.21.0-migration-2026-11-18.md)。
- 使用本机命令行默认 `mvn` 3.10.0 或以上。按实际模块范围用 `-pl ... -am` 增量编测，独立输出复用合法缓存，并发按资源选择，最终执行一次对应完整构建。构建和 CI 命令及业务合同见[开发手册](../../docs/maintenance/repository-development-workflow.md)。
- 公共合同使用共享 record、enum 或 sealed 分支，入口严格解码并保持版本和历史持久数据兼容。沿实际生产者、全部消费者、归档与重放验证，不以仅编译或 HTTP 200 作为动作资格。
- 业务重载使用现有 Quarkus dev 或受管接续入口。涉及 Native 装载、同局恢复、日期推进、保存及 UNKNOWN 行为时读[智能体工作手册](../../docs/maintenance/autoplayer-workflow.md)和[实机与机器授权](../../docs/maintenance/ck3-operating-authority.md)。只读证据、Writer 权威和动作许可均使用各自真实来源。
