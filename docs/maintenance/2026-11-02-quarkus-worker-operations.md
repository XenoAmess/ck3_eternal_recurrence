# 普通 worker 的 Dev 启动与更新操作

普通游玩与同局恢复默认使用 Quarkus Dev。普通 `RootOrdinaryWorkerMain` 仅供运行 owner 明确选择的紧急回退；不要继续默认套用历史 plain 模板，也不要同时启动第二个业务委托。当前机器的运行模式、owner／配置、构建输出、Native 库目录及启动清单由运行 owner 的私有投影管理。

启动要使用已审来源组成的独占源码和构建输出，保留当前运行 tuple 的资源配置。正式源码与当前运行源码有差异时，不整树覆盖正在游玩的版本。运行 owner 先完成当前动作和保存收尾、确认旧 Java 实际退出与资源释放，再由已审 launcher 启动同一 Game 的唯一新委托；原账本和 UNKNOWN／ACK 保持原件。

| Dev launcher 必要输入 | 本次实际使用的选择 |
| --- | --- |
| JDK／固定 Quarkus 版本 | JDK 21；`io.quarkus.platform:quarkus-maven-plugin:3.40.1.1:dev` |
| reactor | 独占项目 POM，`-pl local-service -am`，`-DnoDeps=false`；构建输出通过 `ck3.build.root` 指向获准的独占目录 |
| 普通业务入口 | `-Dquarkus.package.main-class=ordinary-worker-dev` 与 `-Dxar.worker.dev.enabled=true`；开发 profile／DEVELOPMENT 宿主成立 |
| 生命周期方式 | 显式 `-Dquarkus.live-reload.instrumentation=false`，覆盖资源配置中的 true；首次使用已审的停止／finally／新 loader 合同 |
| 业务参数 | `quarkus.args` 只传既有 owner JSON 和业务配置两个参数；DevMain 委托普通 worker 执行 `resume` |
| 本地仓库与临时目录 | launcher 的 Maven、派生 JVM 和 bootstrap 环境使用获准投影；Native 库与资源预算随实际机器配置传入 |
| 依赖解析 | 本次离线 bootstrap BOM 解析失败后，获准以 `-nsu` 解析固定既有版本，再启动成功。production compile 成功不能证明 dev bootstrap 的离线缓存完整 |

这些是参数合同，不是可直接复制到任意机器的启动命令。launcher 应保存实际 argv／环境／来源清单并正确处理命令行引号，禁止从本文补造 owner、私有路径或运行权限。当前 default-mode 投影为 `quarkus-dev`；旧 plain 准备器、实际启动器和只更新旧源码树的采用器均要求 `explicit_plain_fallback=true`，准备器将该选择保留到启动清单。默认更新入口则定向活跃 Dev 的实际源码树并自动触发一次扫描，防止只改旧目录却未更新正在装载的代码。

源采用与扫描使用仓库中的 [adopt-and-trigger.py](../../tools/quarkus/adopt-and-trigger.py)。唯一运行 owner 在活跃 Dev 的独占源码目录中调用它，传入已批准单叶、采用前后 SHA-256 和全新证据目录；目录和本地端口取实际运行模式投影。

```cmd
python tools\quarkus\adopt-and-trigger.py --source-root "<SOURCE_ROOT>" --relative-path "<MODULE>/src/main/java/<PACKAGE>/<CLASS>.java" --candidate "<APPROVED_JAVA>" --expected-before-sha256 "<BEFORE_SHA256>" --expected-new-sha256 "<NEW_SHA256>" --evidence-root "<NEW_EVIDENCE_DIR>" --base-url "http://127.0.0.1:<DEV_PORT>"
```

工具核对根 POM 的模块、源码目录包含关系和前后 SHA，原子写入一个 Java 文件后自动发送一次本地 `GET /q/dev-ui/`。证据目录在源码树之外，已有目录拒绝复用；HTTP 正文仅保留最多 64 KiB 前缀。工具不启停 JVM，不改账本，不重放动作，也不自动重试或回滚。模块被根 POM 声明不等于它已纳入当前 Dev reactor，必须另看实际编译和装载回执。

采用前先核对最新业务委托的 `DELEGATE_STARTED`／`DELEGATE_COMPLETED`、LOOP 或 terminal，不能仅看宿主进程存活。失败或已完成的委托应按实际原状态显式恢复，不能由更新工具重新发起业务。每次验收分别保留：源码写入、扫描 HTTP、实际编译／旧委托 finally、同宿主新 loader、新委托同局 LOOP，以及后续 SAVE_CONFIRMED。HTTP 200 和工具退出 0 都不单独证明热更新成功。新委托启动后若恢复静默，先由运行 owner 核对实际线程／持久状态；不要反复 GET 或再次改源来催动恢复。

截至 2026-11-02 09:46:47Z：隔离 reactor 首编译实际 3095 个单元、113.005 秒退出 0；声明的 3099 个源还含本次未选的 4 个 native-diagnostics 文件。Dev 基线已于09:33:46.497030500Z进入同局 LOOP。一个实际方法体源于09:34:56采用并自动触发扫描；旧委托于09:35:07.752403400Z正常完成，同一宿主／出生下的新 loader 与新实例于09:35:10.355517100Z开始。新委托随后在09:46:47.176607700Z因 `settled recovery requires a completed interrupted cycle` 失败，真实栈落于 `OrdinaryCycleTransitions.requireSettledRecoveryFrontier`。新 LOOP／SAVE 均为零，保存仍为交接前的143日；宿主存活不能代替业务恢复成功。功能修复另沿实际原状态进行，本次发布不作完整业务验收。

既有方法体重载、兼容 instrumentation 重定义和新增依赖类是三个分别验收的范围。新增依赖类的软件试验曾在新 runtime loader 下失败、同源码的新私有宿主成功；不要把这次方法体更新外推为新增类也已支持。需要重建宿主时仍沿真实同局交接，不刷新旧命令 deadline 或重派 UNKNOWN。来源与旧边界见[装载事实](2026-11-02-quarkus-worker-loading-boundaries.md)及[本次脱敏来源索引](2026-11-02-quarkus-worker-operations-sources.json)。
