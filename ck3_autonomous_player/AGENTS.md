# CK3 自动游玩

- 先读[智能体工作手册](../docs/maintenance/autoplayer-workflow.md)和[当前迁移记录](../docs/ck3-1.21.0-migration-2026-11-18.md)。操作实机前读[机器和任务权限](../docs/maintenance/ck3-operating-authority.md)，依 Runtime 当前原件确认 owner、Game 和可用动作。
- 使用完整普通规划器与真实“观察 → 决策 → 操作 → 验证”。MCP-first，复用原版事件 registry 和独立后验。新增 CK3 行为先研究原版候选来源与调用者，按[原生 AI 专题](../docs/ck3-native-ai/README.md)保存 exact-build 证据。
- 优先在同一局恢复。仅在确需修改加载输入、Native DLL 或进程不可恢复时重开进程。保留 savedPair、dirty、序号和原动作事实，拒绝重放 UNKNOWN。普通自动 SAVE 以确认物理存档为起点按 365 游戏日执行，规则与必要 checkpoint 例外见工作手册。
- 实际游玩和 P0 功能、性能故障优先。指标为完整墙钟秒数除以新增确认保存日。记录 observed、等待、恢复及失败，零保存日只报实际耗时和原因。
- Python 接入范围按[开发手册](../docs/maintenance/repository-development-workflow.md)与 Java 迁移计划。新增生产流程走 Java，现有兼容消费者按真实生产范围维护。Native 改动同时遵循[原生桥指引](native_bridge/AGENTS.md)。
