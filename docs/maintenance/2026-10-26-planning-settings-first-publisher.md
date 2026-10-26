# 五项普通规划输入的首次发布入口

`machine_id: xenoamess-full-tower-eb9d2c1186`，2026-10-25 22:32 UTC 更新。当前成果是**已封源码候选，已写前三项及 CoA 限额真实请求，未编译、未运行、未产生首场 DATA**。参数按 Root CONFIG03 明确授权选择；缺失的真实来源继续单列。

现有 `RootJavaBootstrapInputs.Item.original` 已能解码、校验、重编码五项输入，但要求原文件存在。新 `org.xar.ck3.control.service.root.RootPlanningSettingsInputsProducer` 提供首次发布入口：固定五槽强类型 Request → 现有唯一字段 codec → 精确输出报价 → 原 `RootBootstrapOutputGuard` 的 CREATE_NEW → 完整字节、原生文件身份读回 → 原 Root 消费者。它不创建新的账本 writer 或 Game 动作。

| 必填 DATA | Request 内部类型 | 唯一字段 codec |
| --- | --- | --- |
| LIFE_SETTINGS | Life：三个实际布尔配置 | RootAdvanceRuntimeFacts.Settings |
| ADVANCE_TIMINGS | Timings：帧数和两项整数毫秒 | RootAdvanceInfrastructureFactory.Timings |
| CAMPAIGN_DEADLINE | CampaignDeadline.Founding | CampaignDeadline / CampaignDeadlineCodec / OrdinaryCampaignSchedule.calendar |
| REMAINING_DOMAIN_SETTINGS | RootRuntimeDomainSettings.Configuration | RootRuntimeDomainSettings |
| NATIVE_DOMAIN_ORIGINALS | RootRuntimeNativeOriginals.Configuration | RootRuntimeNativeOriginals |

Request 还必须明确 schema、机器、观察/复核时间和独立 outputRoot。Clock identity、开始日期/raw、策略、路径和所有嵌套配置都来自真实请求，不推测 seed 或增加存档前置。五个输出文件名固定为 `life-settings.json`、`advance-timings.json`、`campaign-deadline.json`、`remaining-domain-settings.json`、`native-domain-originals.json`。

入口参数为 `QUOTE REQUEST_PATH REQUEST_BYTES REQUEST_SHA256`，或 `CREATE_NEW REQUEST_PATH REQUEST_BYTES REQUEST_SHA256 BINDING_PATH BINDING_BYTES BINDING_SHA256`。后者必须是独立签发、尚有效、价格与整批精确输出一致的真实 Bootstrap binding；源码存在不表示已有此授权原件或输出。

发布前实际读取并保持每个 Native/Python/header 来源、formal/default/override policy、normal-exit 原件、CoA limits、query-history 的独立 request/producer 和可选 Stock 来源。Native 项只做 preGame 来源配置；真正 NativeLaunchPlan cut membership、loaded 身份、初始准入和业务结果继续由原消费者验证。

源审发现初稿调用正长度通用 reader 会拒绝 normal-exit 合法的 **0 B immutable launch-settings snapshot**。后继 17 改为有限 stream 读取并核对完整 length/SHA/native witness，保留该空文件语义；其他类型自己的正长度合同继续有效。旧候选 15 保留历史，不再选其 main。

历史后继 [settings17/SOURCE-DELTA17.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/planner_owner/settings17/SOURCE-DELTA17.json) 保留上述空 snapshot 修复。当前完整选源为 [settings20/SOURCE-DELTA20.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/planner_owner/settings20/SOURCE-DELTA20.json)，4236 B / SHA `b2fe8417812a5720fed029b8643682fbc4a4713c39a0377ef488ebc5286ed76a`，选择 20 的 main 与 test。测试源码覆盖真实临时文件 → publisher → 原 Guard → 输出 → 原 codec 与 generic consumer、错误字段/缺字段/类型、来源漂移/过期、日期/raw 冲突及禁止二次发布；**尚未执行**。

20 在同一类增加 `CoreRequest` 与 `CORE_QUOTE/CORE_CREATE_NEW`，仅发布前三项纯配置，不把尚缺 Native cut 或 NormalExit 原件作为前置。原固定五槽 `Request` 保持必填来源要求。`CoaLimitsRequest` 与 `COA_QUOTE/COA_CREATE_NEW` 使用唯一 `CoaVfs` codec 首发限额原件。同一 Prepared/Guard 写入路径支持这三种封闭输出计划；没有另建 runner、修改共享 CLI、Kind 或 Guard。

QUOTE 现在调用原 `RootBootstrapProtocol.OrdinaryQuote` 与 `emit`，输出唯一 LF 帧；阶段分别为 `CORE_SETTINGS`、`COA_READ_LIMITS`、`PLANNER_SETTINGS`。这是实际准入消费者接收的 `phase-quote/v1` 合同，已与 Readiness 核对；原自定义 QUOTE receipt 不再作为入口。

真实 raw requests 在本场 `requests/planner-core-request20.json`（614 B / `eac339d51ef3e7ebd4c167ff7f1cba92178b6989c3228e5cd1ffd0a26745f374`）与 `planner-coa-request20.json`（363 B / `f401ce7c07cf899295b1314ed3ad8a854a22df58deab36c7238625a0b6d76845`）。资产与 control 各用独立 `planner/core`、`planner/coa-read-limits` 子目录，不与 query-history 输出混合。目录当前仅有 mkdir/stat 事实，尚无原生发行者 witness 或 binding。

明确选择为 Life 三项 true、4096 帧、命令 30000ms、推进 300000ms。计划日期来自当前安装书签原件的 `1066.9.15`；现有 Java fixed365 公式给出 raw53144328、360 月，独立 clock ID 为 `root-robert1066-resume61-20261026`。这只是计划配置，实际 Origin、actor、Game 与成绩仍只能来自真实 Entry。Lifecycle 选择唯一 `java.native-driver.life-advance.v1`、30000ms actionBudget；七个 PlanFlags 全 true，但不赋予私有动作资格。完整选择、实际 repository policy 原件与理由见 [SETTINGS-VALUES20.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/planner_owner/SETTINGS-VALUES20.json) 和 [SETTINGS-REQUEST-INPUTS20.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/planner_owner/SETTINGS-REQUEST-INPUTS20.json)。

剩余域的 NormalExit 三原件、CoA 发布成品、query-history document，以及当前唯一 Native originals 合同要求的全部同一 qualified ordinary cut 来源均未准备，完整五槽请求尚未生成。query-history 独立 rawRequest04 已由唯一 owner 写出；它仍缺实际 NativePlan、最终 producer 与 binding。源码、计划日期、配置原件和历史 research cut 都不替代这些成品。

后继实际 source 读回：current R5 的 `RootRuntimeNativeOriginals.SCHEMA` 已是严格 `v7`，新增 mandatory `ARMY_SUPPLEMENTAL_WAR_NATIVE → native_bridge/src/ck3_11906.cpp`，原件映射由 NativeSupply 的 [SOURCE-MAP30.json](D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/native_supply/local30_supplemental_rolefix/SOURCE-MAP30.json) 独占维护。此 source 采用不代表编译、v7 首场产件或 Native cut 资格。settings20 主类泛型消费唯一 Configuration/codec，不写死 v6/角色数量；其 fixture 使用 `Role.values()` 和唯一 `SCHEMA`，本岗没有并行改合同。后续完整请求只按真实同 cut 来源生成 v7 全角色配置；Source60 类型导航和 mutable dev61 文件都不补入这份尚缺的 actual manifest。

2026-10-26 实际执行补注：机器 `xenoamess-full-tower-eb9d2c1186`，Readiness 结果索引观察于 `2026-10-26T05:45:43.747208+00:00`。原 `SourceGraphJavaIntent CLASS` 经真实 regular Jars 执行上述两个 raw20 请求，`CORE_QUOTE` 与 `COA_QUOTE` 均取得 terminal PASS、child exit0、Job active0、input pre/post 与 runtime 三项 MATCH；耗时分别 1.3396262s 与 1.4421055s。这里是两条真实 Java QUOTE 路径成功，未运行本专题 JUnit，也未 CREATE_NEW。

本岗已实际读回两份 stdout 与 terminal，精确 length/SHA 均匹配原索引 [ACTUAL-QUOTE-RESULTS02.json](D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/metadata/ACTUAL-QUOTE-RESULTS02.json)，17686 B / `d3cee9a1df7dbed17bd76d41d20b89794bb81025aa952fa4c7e1dfe6cd293afe`。两份 stdout 都是原 `phase-quote/v1` 单 LF 帧、authority 为 `AWAITING_REAL_INDEPENDENT_ISSUER_BINDING`：

- [CORE_SETTINGS stdout](D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/readiness/quote05/stdout.log)：816 B / `4af3d840d2c27ba65d9b8ba35fde2061c115c1fd27256a77daa503a66b3ddcfe`；三个计划输出分别为 Life 135 B、Timings 130 B、Deadline 3515 B。
- [COA_READ_LIMITS stdout](D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/readiness/quote06/stdout.log)：528 B / `1937a83d879dbd4344bfad5527e743132673ec47fcfb57b6e109ffa67844a92d`；一个计划输出 119 B。

这些 output length/SHA 是精确发布计划，不能当作已存在 DATA 或 CoA 原件。真正 CREATE_NEW 仍须独立发行者的有效 binding 与原 Guard，五槽 aggregate 继续等待实际来源；以上执行不授予 Native cut、Loaded、Entry、Game、SAVE 或 G2 完成。

Host 仍是可复用 R5 mutable/Maven 的唯一 writer；后续先局部编译和受影响测试，再做最终完整验收。本专题没有取得全图、实机或 G2 完成信用。存储遵守统一 101/102 额度，08:00 UTC 财务复核；资料 2026-11-01 21:53 UTC 用途复核，未自动续期。
