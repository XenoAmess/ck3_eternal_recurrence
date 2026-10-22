# Java 地图回执的真实 HTTP 差分门禁

一期的切换点是 `POST /v1/map-admissions/compose` 产出地图回执。Python 客户端只验证并保留 Java 返回的原始字节，不调用 Python producer 兜底；原 owner parser、Queue camera/FULL 守卫、feeder 与 reducer 继续消费原合同。

这是 CI 接线方案，尚不表示 hosted CI 或当前游戏通过。2026-10-22 的本机实际 Maven 与冻结 N46 软件全链已单独记录在[软件证据](evidence/java-map-phase1-http-all-consumers-20261022.json)，之后 Java 共享构建和服务 owner 的本机整链记录在[独立证据](evidence/java-control-build-and-owner-http-20261022.json)。它们不能外推 hosted CI 或真实游戏结果。实际执行必须另有带 `machine_id`、时间、源码和完整部署绑定的回执。本机 D: 启动草稿不是 CI 输入，CI 不能依赖它。

用户随后明确要求新增模块全部使用 Java。共享构建、受限进程和 CI 服务 owner 将使用 Java 入口；既有 Python 客户端和已通过的消费者回归保留用于验证旧链。未执行的 Python CI 草稿已由 Root 精确移出仓库，来源机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，历史路径为 `D:/codex-ck3-demos/2026-10-22-java-phase1/logs/RETIRED-UNDELIVERED-PYTHON-CI-DRAFT01.py`；它不能作为正式入口、CI 输入或通过证据。

## 字段与来源边界

- 这条 Python↔Java 链保留 opaque Python JSON 整数域，FILETIME 为 1 至 `2^64-1` 的整数；Java 使用 `BigInteger`，不能经 `double`、`long` 截断或 JavaScript Number。跨 JS 的规范十进制字符串合同单独验证，不能冒充这条链的 FILETIME 字段。
- 请求上限 65,536 B，响应上限 16,384 B；后者对应原 Queue 读取上限。错误字段、缺字段、`null`、`[]`、布尔/浮点身份、未知字段和重复 JSON 键均须执行真实拒绝路径。
- 成功响应必须与既有 Python producer 的 canonical UTF-8 字节逐字节相同；包括大整数、中文、emoji、控制字符和原样保存的 UTC 字符串。Python producer 在测试中只作差分 oracle，返回给消费者的始终是 Java 原始响应。
- 服务身份使用完整 `quarkus-app` 文件清单、原 Maven 实际终态、Java 源码 pins、原进程 PID/出生十进制串/EXE、原生 TCP listener→PID 绑定和 HTTP identity；`quarkus-run.jar` 单件不能证明部署闭包。

## 独立 CI step 的完整命令组

CI 先完成显式 JDK/Maven 工具链资格和完整 reactor `verify`。构建输出、Maven repository、TEMP、日志都写到 runner 的获准任务根；不得默认写系统卷。取 exact Source32 历史输入需要 `actions/checkout` 的 `fetch-depth: 0`，公开 archive tag 必须存在。缺依赖或来源时直接 RED。

随后由可移植、仓库内的 Java 服务 owner 建立一个 loopback 服务，测量完整 fast-jar 闭包并写 `xar.java-map-service-running/v1` 小回执；将其绝对路径设置到 `XAR_JAVA_MAP_SERVICE_EVIDENCE`。此 owner 需要接收显式 work root、构建回执和 Java EXE 参数，不可固化本机盘符。构建复用同一共享 Java 生产入口，不在 CI owner 另写 Maven producer。CI 中只有该 owner 启停服务；实机一期由 Root 接管同一服务继续使用。

Python 搜索路径使用平台分隔符，仓库根、`ck3_autonomous_player/src` 优先；调用者显式配置的既有 Python 依赖目录随后追加，不固化本机 checker 盘符。静态检查的 `MYPYPATH` 只包含仓库根及 SDK 源码。禁止通过关闭 `import-untyped` 隐藏路径缺失。`PYTHONDONTWRITEBYTECODE=1`，关闭 mypy cache。

```text
python -B -X utf8 -m mypy --strict --strict-equality --explicit-package-bases --follow-imports=silent --no-incremental --cache-dir nul tools/g2_saved_campaign/java_map_admission_client_v1.py tools/g2_saved_campaign/test_java_map_admission_v1.py
python -B -X utf8 -m unittest -v tools.g2_saved_campaign.test_java_map_admission_v1
```

Windows step 使用 `cmd`，每条命令之后立即检查并传播 `%errorlevel%`。完整新模块的实际静态检查范围和测试数分别记录。缺 Java/Maven、服务未启动、无实际服务回执或进程/来源漂移必须 RED；`setUpClass` 明确抛错，不得 `SkipTest` 或以零发现/跳过计通过。

新增 Java 实现位于独立 `java/ck3-control/build-tools`，不修改一期冻结 parent。`ControlBuild` 是唯一共享构建生产入口；`WindowsJobProcess` 使用固定 JNA 的原生 Windows Job 先挂起创建、加入硬内存限制后续行，记录原进程出生、EXE、退出码与 Job 实际终态。`MapAdmissionServiceOwner` 消费新构建回执、建立完整部署 manifest 和原生 TCP listener→PID 绑定；`MapAdmissionCi` 调用这个 owner，再执行上面的完整 Python 命令组，并检查实际发现六项、零跳过和服务闭场终态。CI 运行闭包由 standalone POM 的 jar manifest 和 `lib/` 交付，不能猜本机 Maven cache 路径。

共享构建和新 owner 已取得上述独立本机证据；后续新增 bootstrap、typed capacity、构建回执与 reactor module 仍须重新完整验证。workflow 的独立 Java step 使用安装在 runner 上的 JDK21，先以标准 JDK source-launcher `CiBootstrap.java` 运行当前默认 `mvn --version`，核对实际稳定版本、安装 home 和 launcher，再执行 standalone 完整 `verify`。这个最初 bootstrap 没有预先存在的 JNA Job 硬限制，其计划明确保存 `bootstrap_native_job_hard_bound=false`、`bootstrap_alone_grants_pipeline_qualification=false`，不能独立授予正式通过。

2026-10-22 14:19Z 的[新合同与 manifest 修复证据](evidence/java-control-owner-manifest-repair-20261022.json)记录正式默认 `mvn` 工具构建 22 项零跳过、已资格化九模块 458 项零跳过，以及新 owner 的完整两模块静态检查、六项真实 HTTP 和三条原消费者路径。实际 66,728 B program manifest 已通过原 Python 的 1 MiB reader；小回执仍为 64 KiB。参数错误的 03 与共享上限错误的 04 原 RED 均保留。该证据不表示 hosted bootstrap 已执行，也不覆盖后续未纳 parent 的迁移家族。

Maven 的后续规范是消费默认 PATH 命令 `mvn` 并实核版本，生产最低要求为稳定版 `>=3.10.0`，允许更新的稳定版；用户机器在自己的原安装位置升级，不要求迁址，也不锁定某台机器的 `C:/apache-maven`。CI 已有合格的默认 Maven 时直接沿用，不下载、不改 PATH 或 `GITHUB_PATH`，不改变安装位置或默认选择。当前 bootstrap 在缺失、旧版或预发布版环境明确 RED，要求先完成原位置升级；它不私自在任务目录创建另一份默认安装。工具包的 source-launcher、缓存和部署任务目录不等于 Maven 的安装位置。Plan 保留观测得到的实际分发路径作来源事实，不能据此自动生成用户 override。此前本机回执记录的实际路径原样保留。

随后 `ControlCi` 使用共享原生 Job 和唯一 `ControlBuild` 重新完整构建工具包，执行真实 Job/TCP/JSON/bootstrap 回归，改用新构建的完整 jar/lib 闭包，执行预期 Maven 失败路径、当前完整 reactor、完整两模块静态检查和六项真实 HTTP 消费者测试，最后必须观察服务 Job0。缺环境、退出失败、超时、零发现或跳过均为 RED。当前 checkout 保持 `fetch-depth: 0`；每条 cmd 命令消费实际退出码。上传保留七天的小型 JSON/XML，不上传 JAR、Maven cache 或整棵任务目录。

CI 每次运行读取[共享存储策略](../storage-retention-policy.json)，观察实际执行卷与系统卷的总量和可用空间，并记录当前机器。只有默认项目配额不足时才使用[获准 CI profile](../../java/ck3-control/ci-profile.json)的 8 GiB 上限；override 绑定实际文件 SHA、owner、task、reason，90 分钟到期。它只调整项目配额，实际 free-space、安全余量和显式系统增长预留公式不变。工具、缓存、部署、临时文件都留在当前 runner 的新任务根，不能套用本机历史容量授权或从 runner 规格推断卷容量。启动共享工具还须将 `-Djna.tmpdir` 指向这份当前容量回执的 `temporary_root`。

## 必须执行的生产者到消费者路径

`test_java_map_admission_v1.py` 包含真实 HTTP 正反例，以及三种既有 closed lineage：普通闭场、readiness projection、FULL pre-dispatch local rejection。真实 Java producer 接入原有 emitted qualifier、owner、原 Queue camera/FULL 完整方法与真实 reducer。仅旧夹具的外层 Game/录制输入保持 RAM seam，Java HTTP 和 Java 进程身份不可 mock。

独立负例可注入损坏响应/网络错误，但回执必须标明 `injected-test/v1`，不能当成实际 Java HTTP 成功。真实 HTTP output-cap 拒绝另行覆盖，不得转 Python producer。

Java JUnit、Python 局部 parser 或完整固定点 fixture 均不能代替上述整链；这些软件检查也不授予当前实际 Native32/67 图、warm、游戏推进、G2 完成、30 年完成或 1 秒/日性能资格。当前场次仍须由 Root 使用同一来源绑定的 Java 服务产实际地图回执，再经冻结消费者和真实 FULL/SAVE 后验验证。
