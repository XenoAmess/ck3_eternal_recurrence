# Quarkus 嵌入 Maven 错误缓存路径

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际观察：2026-10-30T00:59–01:05Z。仅证明本机本次 DEV65 启动，不外推其它机器。

Java 源码已编译，但 Quarkus DEV 解析四个已有依赖失败。外层默认 `mvn` 使用获准 D 盘缓存；仅查看该缓存的 JAR、仓库标识或配置 getter，不能证明嵌入解析器实际也使用该路径。

唯一 `-X` 启动的真实日志给出差异：外层两个 `EnhancedLocalRepositoryManager` 使用 `D:/codex-ck3-demos/2026-10-22-java-phase1/m2`，嵌入解析器却使用 `Z:/codex-ck3-demos/2026-10-22-java-phase1/m2`。此前 settings mirror、额外 repository、四文件 central 别名、显式环境变量等尝试均失败；不把它们写成有效修复。

有效差异是让已有启动进程明确以既有 D 盘开发根为工作目录：`Popen(cwd=...)` 或工具的 `workdir`，本次为 `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control`。保持原默认 `mvn`、源码、输出和依赖缓存；未复制仓库、修改全局设置或重启 CK3。下一次真实日志的三个 manager 均落正确 D 根，四坐标错误消失，01:03:58.258Z 新业务 PID330244 启动，HELLO77及普通循环43真实接回同 Game171676。

本次只运行业务，插件已证实的 `-Dquarkus.generate-code.skip=true` 避免无需求的 TEST bootstrap；它是 Maven 插件参数，业务启动时出现相同名称的未知运行配置警告不等于插件未跳过。测试未运行，不授测试通过信用。

原件：`D:/ck3-state/ck3-java-g2-resume63-vanilla01/artifacts/persistent-java02/dev-resume65/attempt08/stdout.log` 与 `attempt09/ACTUAL-REPOSITORY-CWD-FIX.json`、`ACTUAL-HELLO.json`。八次失败和实际处理保留在[当前记录](../autonomous-agent-progress/2026-10-29-java-g2-resume64-current.md)。这份记录不增加后续启动审计；真实同类故障直接复用已验证的工作目录修复。
