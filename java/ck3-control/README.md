使用 JDK 21 和命令行默认的 Maven（不低于 3.10.0），从仓库根目录启动现有 Quarkus 开发宿主：

```cmd
cd java\ck3-control
mvn -pl local-service -am quarkus:dev -Ddebug=false
```

`-am` 纳入宿主依赖的 reactor 模块。日常 Java 修改交给 dev mode 编译和重载，保留同一开发进程；每个领域模块无需另开服务。需要外置构建输出时，追加 `-Dck3.build.root=<获准的绝对输出目录>`，本地 Maven 仓库同样遵守当前工作包的空间预算。

开发配置已启用 `%dev.quarkus.live-reload.instrumentation=true`。兼容的方法体变化可通过 instrumentation 生效；类型结构、CDI 或配置变化仍可能触发应用内部重新初始化。热重载不能证明内存状态、唯一 writer 或 UNKNOWN 状态自动保留。已冻结的 SDK、runtime 和验收包仍以其实际来源为准。

2026-10-23 本机验证（`machine_id: xenoamess-full-tower-eb9d2c1186`，Quarkus 3.40.1.1）：在独立的 32 文件源副本中修改现有状态接口，第二轮于 `09:12:30Z` 完成 A→B→恢复。三个响应均来自 PID `247468`、出生 FILETIME `134372203427616096`；记录到一次启动、两次 instrumentation 重载、零次应用完整重载、零次 Maven 重启。启动到首响应、修改到新响应、恢复到确认响应的墙钟分别为 25.085、2.632、1.520 秒，包含轮询和回执落盘，不作性能对比。

整轮资源结果仍为 **RED**：原生 Job 峰值 `2222022656 B` 超过 `2147483648 B` 预算。受控退出码为 `143`，最终活动进程为零，原始源文件已恢复；不能将其报告为 Maven verify、CI 或实机通过。第一轮的恢复轮询失败及两轮资源失败均保留。

第二轮原始证据：`D:/codex-ck3-demos/2026-10-22-java-phase1/build/quarkus-devloop-20261023-02/evidence/actual.json`，4076 B，SHA-256 `1f8cd69869afdbc4447ac9937d922066a76b56ef676f418b0df23275f8d88650`。这份证据只覆盖状态接口的开发重载，不扩大到 G2、SDK 或游戏续接。

[Quarkus 官方开发模式与 instrumentation 文档](https://quarkus.io/version/3.40/guides/maven-tooling/)。
