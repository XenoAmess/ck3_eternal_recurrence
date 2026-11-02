# Quarkus worker 装载事实与重载边界

2026-11-02：当前游玩进程继续使用原版本。Main301 的冻结参数直接指定 `RootOrdinaryWorkerMain`，模式为 `resume`；同名现持源码的 `main` 调用 `new RootOrdinaryWorkerMain().run(args)` 后退出，没有启动 Quarkus。类上的注解、`QuarkusApplication` 接口及类路径中的 Quarkus JAR 不会自行启用 dev。当前普通入口继承既有启动模板；最初选择普通入口的决策或从 dev 回退的记录未持有，不能写成 dev 已证不可用。

既有 [RootOrdinaryWorkerDevMain](../../java/ck3-control/local-service/src/main/java/org/xar/ck3/control/service/root/RootOrdinaryWorkerDevMain.java) 要求开发 profile 和 `DEVELOPMENT` 宿主、显式选择 `ordinary-worker-dev`、`xar.worker.dev.enabled=true` 同时成立。它接收 owner 与配置两个参数，委托原普通 worker 执行 `resume`。停止时只请求协作收尾；实际业务 `finally` 完成后才清理自己创建的停止标记并释放 dev 锁。超时不代旧 worker 清理或中断 Native 调用；附着会话关闭只释放连接与附着句柄，不停止 Game。普通入口不取得这把 dev 锁，因此锁本身不能证明它与普通 worker 互斥。

Quarkus 3.40 文档明确支持 command mode 的 dev 启动；本项目现持 POM 固定版本为 3.40.1.1。应用重启会重建用于热部署类的 Runtime ClassLoader，不能据此推断所有现存对象都原地更新。[Command mode development mode](https://quarkus.io/guides/command-mode-reference/#development-mode)，[Class loading reference](https://quarkus.io/guides/class-loading-reference/)。

当前配置启用 `%dev.quarkus.live-reload.instrumentation=true`，兼容的类变更可能通过重定义避免完整应用重启；旧生命周期试验明确使用 `false`。两种方式的验收范围分开，兼容重定义不能替代旧委托退出和新委托取得所有权的证明。[Quarkus Maven instrumentation 配置](https://quarkus.io/version/3.40/guides/maven-tooling/)，[生命周期事件](https://quarkus.io/guides/lifecycle/#listening-for-startup-and-shutdown-events)。

| 既有回执 | 实际结果与适用范围 |
| --- | --- |
| resume63 多模块 v4 | 依赖源 A→B 在同一 JVM、新 runtime loader 下通过；旧资源 `finally` 先于新业务，真实 FileLock 有效。业务失败不自动重试，显式后续重载可继续。断言退出 0 与 Maven 包装退出 1 分列保留；这是软件替身验证。 |
| resume63 超时回归 | 旧业务仍持锁时新委托报告 ownership busy；旧业务实际 `finally` 后后继才开始，没有中断旧业务。 |
| resume64 新增依赖类 | 已更换 runtime loader，新增类文件存在，热请求仍 500／`NoClassDefFoundError`，资源查询为 null；同源码的新私有宿主成功。此配置边界不能推广为所有 dev 不支持新增类，也不能用一次应用重启保证修复。两次包装退出 1 保留。 |
| resume64 旧 Game 观察 | 新 dev 宿主曾连接原 Game 并进入 LOOP，随后 `PLANNER_STOPPED`、零新增保存；它不构成当前游玩进程的热重载验收。 |

Main301 的 760 是有序类路径条目数。有限比对覆盖 36 个显式生产输入源：运行源码经 LF 归一化 36 项匹配，正式源码 27 项匹配、9 项有差异；不能据此宣称整个类路径或 Maven reactor 等价。四个入口类的首解析路径已记录，但原编译源 pin 未持有，当前同名源码不能倒授为已装载类的精确来源。

后续若另行安排 dev 接续，应先固定源与二进制输入及隔离输出，完成原业务委托和 Runtime 所有权交接，再分别验证既有方法体重载与新增依赖类；原账本、UNKNOWN、ACK 和同局身份保持原件。当前阶段只留存事实与来源，不切换入口、不重启 worker 或 Game。保存进度与性能仍按独立运行回执记录。

[脱敏来源索引](2026-11-02-quarkus-worker-loading-sources.json)保存具名回执的相对导航与 SHA-256；完整源码、原始日志、类路径及机器配置留在执行机。研究使用两份完整模型答复，均整稿未采用；本次没有新增 Java 编译、JVM、Maven 或 Game 操作。
