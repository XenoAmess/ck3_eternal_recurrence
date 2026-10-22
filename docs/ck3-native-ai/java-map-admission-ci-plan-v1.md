# Java 地图回执的真实 HTTP 差分门禁

一期的切换点是 `POST /v1/map-admissions/compose` 产出地图回执。Python 客户端只验证并保留 Java 返回的原始字节，不调用 Python producer 兜底；原 owner parser、Queue camera/FULL 守卫、feeder 与 reducer 继续消费原合同。

这是 CI 接线方案，尚不表示 hosted CI 或当前游戏通过。2026-10-22 的本机实际 Maven 与冻结 N46 软件全链已单独记录在[软件证据](evidence/java-map-phase1-http-all-consumers-20261022.json)，不能外推 hosted CI 或真实游戏结果。实际执行必须另有带 `machine_id`、时间、源码和完整部署绑定的回执。本机 D: 启动草稿不是 CI 输入，CI 不能依赖它。

用户随后明确要求新增模块全部使用 Java。共享构建、受限进程和 CI 服务 owner 将使用 Java 入口；既有 Python 客户端和已通过的消费者回归保留用于验证旧链。未执行的 Python CI 草稿已由 Root 精确移出仓库，来源机器为 `machine_id: xenoamess-full-tower-eb9d2c1186`，历史路径为 `D:/codex-ck3-demos/2026-10-22-java-phase1/logs/RETIRED-UNDELIVERED-PYTHON-CI-DRAFT01.py`；它不能作为正式入口、CI 输入或通过证据。

## 字段与来源边界

- 这条 Python↔Java 链保留 opaque Python JSON 整数域，FILETIME 为 1 至 `2^64-1` 的整数；Java 使用 `BigInteger`，不能经 `double`、`long` 截断或 JavaScript Number。跨 JS 的规范十进制字符串合同单独验证，不能冒充这条链的 FILETIME 字段。
- 请求上限 65,536 B，响应上限 16,384 B；后者对应原 Queue 读取上限。错误字段、缺字段、`null`、`[]`、布尔/浮点身份、未知字段和重复 JSON 键均须执行真实拒绝路径。
- 成功响应必须与既有 Python producer 的 canonical UTF-8 字节逐字节相同；包括大整数、中文、emoji、控制字符和原样保存的 UTC 字符串。Python producer 在测试中只作差分 oracle，返回给消费者的始终是 Java 原始响应。
- 服务身份使用完整 `quarkus-app` 文件清单、原 Maven 实际终态、Java 源码 pins、原进程 PID/出生十进制串/EXE、原生 TCP listener→PID 绑定和 HTTP identity；`quarkus-run.jar` 单件不能证明部署闭包。

## 独立 CI step 的完整命令组

CI 先完成显式 JDK/Maven 工具链资格和完整 reactor `verify`。构建输出、Maven repository、TEMP、日志都写到 runner 的获准任务根；不得默认写 C:。取 exact Source32 历史输入需要 `actions/checkout` 的 `fetch-depth: 0`，公开 archive tag 必须存在。缺依赖或来源时直接 RED。

随后由可移植、仓库内的 Java 服务 owner 建立一个 loopback 服务，测量完整 fast-jar 闭包并写 `xar.java-map-service-running/v1` 小回执；将其绝对路径设置到 `XAR_JAVA_MAP_SERVICE_EVIDENCE`。此 owner 需要接收显式 work root、构建回执和 Java EXE 参数，不可固化本机盘符。构建复用同一共享 Java 生产入口，不在 CI owner 另写 Maven producer。CI 中只有该 owner 启停服务；实机一期由 Root 接管同一服务继续使用。

Python 搜索路径使用平台分隔符，包含仓库根、`ck3_autonomous_player/src` 和 `tools/g2_saved_campaign`。静态检查的 `MYPYPATH` 也须包含仓库根及 SDK 源码。禁止通过关闭 `import-untyped` 隐藏路径缺失。`PYTHONDONTWRITEBYTECODE=1`，关闭 mypy cache。

```text
python -B -X utf8 -m mypy --strict --strict-equality --explicit-package-bases --follow-imports=silent --no-incremental --cache-dir nul tools/g2_saved_campaign/java_map_admission_client_v1.py tools/g2_saved_campaign/test_java_map_admission_v1.py
python -B -X utf8 -m unittest -v tools.g2_saved_campaign.test_java_map_admission_v1
```

Windows step 使用 `cmd`，每条命令之后立即检查并传播 `%errorlevel%`。完整新模块的实际静态检查范围和测试数分别记录。缺 Java/Maven、服务未启动、无实际服务回执或进程/来源漂移必须 RED；`setUpClass` 明确抛错，不得 `SkipTest` 或以零发现/跳过计通过。

## 必须执行的生产者到消费者路径

`test_java_map_admission_v1.py` 包含真实 HTTP 正反例，以及三种既有 closed lineage：普通闭场、readiness projection、FULL pre-dispatch local rejection。真实 Java producer 接入原有 emitted qualifier、owner、原 Queue camera/FULL 完整方法与真实 reducer。仅旧夹具的外层 Game/录制输入保持 RAM seam，Java HTTP 和 Java 进程身份不可 mock。

独立负例可注入损坏响应/网络错误，但回执必须标明 `injected-test/v1`，不能当成实际 Java HTTP 成功。真实 HTTP output-cap 拒绝另行覆盖，不得转 Python producer。

Java JUnit、Python 局部 parser 或完整固定点 fixture 均不能代替上述整链；这些软件检查也不授予当前实际 Native32/67 图、warm、游戏推进、G2 完成、30 年完成或 1 秒/日性能资格。当前场次仍须由 Root 使用同一来源绑定的 Java 服务产实际地图回执，再经冻结消费者和真实 FULL/SAVE 后验验证。
