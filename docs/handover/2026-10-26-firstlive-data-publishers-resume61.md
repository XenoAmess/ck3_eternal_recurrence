# 首场 DATA 发布链与能力配置首发（resume61）

`machine_id: xenoamess-full-tower-eb9d2c1186`。本文记录本轮各 sole owner 的实际源码答复与本岗施工，观察窗口为 2026-10-25 21:40 UTC 起；不是编译、Native、Game 准入或 M0–M7 业务验收。Event 已转述 Root 明确选定角色 22 的现有历史 manifest；本岗尚未接收其他角色的新首场实际原件，不能将此范围外推成其他岗位永久没有原件。

## 当前安装与离线来源

共享安装见证为 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/formal_release/INSTALLATION-WITNESS02.json`，3032 B，SHA-256 `49f08808eb15dd2eb2d24d05f400c7dd68cf1d4d7de14741e2efbbd7417c339c`，观察于 `2026-10-25T21:43:36.139626Z`。

当前 CK3 `Z:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe` 的实际 stat 为 101040248 B、FileID 十进制字符串 `281474999561719`、`mtime_ns` 字符串 `1792597384296669700`；三者与旧完整哈希观察一致，本轮复用旧 SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，没有再次全读大 EXE。新鲜小文件读回给出 launcher `rawVersion=1.20.0.4`、appmanifest `buildid=25734779`、`BetaKey=1.20.0`。01 中 BetaKey 的 `null` 来自大小写敏感的字段提取，不能解释成分支不存在；02 保留该修正来源，01 不覆盖。

后台真实 Steam probe 为同目录 `STEAM-OFFLINE01.json`，`2026-10-25T21:40:42.524749Z`，`status=offline`、`offline_mode=true`，PID `239464`、出生 FILETIME 字符串 `134373773866190684`、版本 `11.15.70.27`；既有原生 provider 两次读取均为 1，工具退出 0。未操作窗口、截图、切换在线或启动游戏。将来 CREATE 前仍由原 Java 准入重新获取足够新鲜的见证；这些准备回执不是启动卡或 loaded 资格。

## 22 个必需角色的真实首发入口

| 序号与角色 | sole owner / 原始发布路径 | 当前施工边界 |
| --- | --- | --- |
| 01 FAMILY_DOMAIN | RA + Family：`RootJavaBootstrapInputs.FamilyRequest` → `prepareFamily` → 唯一 `RootFamilyInitialDataProducer` | 修正请求后实际 quote08 PASS，三槽计划 81/94/82 B；原路径错误与严格缺 `child_matrilineal` 的两 RED 保留，尚无实际 DATA |
| 02 CHILD_MATRILINEAL_DOMAIN | 同上，独立必需槽 | 不把缺失、null 或空集合混成 ABSENT |
| 03 DEFAULT_MARRIAGE_DOMAIN | 同上，独立必需槽 | 与前两项同一实际 Guard 路径 |
| 04 INITIAL_PREPARED_ENVIRONMENT | Launcher：`RootProfileBootstrapCommand.Mode.PROFILE` → ProductionInventory/ProfileAssets/PROFILE_ENVIRONMENT → `Inputs.environment` → 原 Guard | preGame；需要实际 qualified SERVICE/flatTools、生产请求、生产 manifest、独立 issuer；没有第一帧前置 |
| 05 INITIAL_POLICY | 原 `Inputs.initialPolicy` → 原 Guard → `InitialEpisodePolicy.readExact(...).verify()`；Event17 合入 `RootInitialPolicyBootstrap` 非交互 schema 路由 | 必须已有真实 ENV；native_protocol_identity/initial_policy01 提供窄适配。Launcher 的 source13 交互 Session 路由是未采用备选，不应成为额外首场前置；底层实际 producer 仍由两个 owner 核对 |
| 06 ORIGINAL_DRIVER_RUN_PROFILE | Driver + Launcher：`RootOriginalDriverRunProfileProducer.prepare` → 原 Body/Guard CREATE_NEW | v4 文件，真实 machine/time/session/environment/lifecycle/noPact/import 输入；不要求第一帧 |
| 07 EXPLICIT_FRESH_PACT | **与 06 相同的实际 v4 FileRef**；Ledger 拥有来源绑定 getter 与真实 consumer | 显式 `ordinary_campaign_no_pact`；不另造 pact 文件或第 23 DATA |
| 08 CAPABILITY_CONFIGURATION | 本岗：`RootCapabilityInputsProducer` → 原 capability codec → 原 Guard | 原 935 B grouped Request 已真实 Java decode/QUOTE PASS，计划输出 339 B；独立 issuer/CREATE 仍未执行，DATA 未生成 |
| 09 CAPABILITY_SESSION_PRESENTATION | 与 08 同一次实际发布；显式 `FRESH_NEW_EPISODE` 启动参数与真实路径保管 | 同次 QUOTE 计划输出 398 B；不授实际 episode binding、Driver cache 或 native Game 事实，实际初始化仍在首帧后；无 DATA |
| 10 SWAY_CONFIGURATION | Sway：`RootSwayConfigurationProducer.Request` → prepare/quote → 原 Guard/CheckpointFiles CREATE_NEW → readExact | Fresh 消除未来 ReadRef 循环，Import 校验保留；实际 quote04 PASS，计划输出 611 B，无 CREATE/DATA。真正初始化仍消费 Start/Driver 后的实际 proof |
| 11 MCP_CATALOG | Public：`RootOriginalMcpCapture.measure/capture` | 由 source-pinned 原 registration 做离线 No Game 查询，产生原 catalog |
| 12 MCP_ADMISSION | Public：`RootPublicMcpAdmission` 两阶段 typed publisher，admission50 已封 | quote-bootstrap/bootstrap 消费实际 capture + NativePlan + Guard，产生显式临时 UNMIGRATED；经原 Definitions publisher/readExact/Factory 的真实绑定，再 quote-qualify/qualify 独立 final admission；不能把 registration facts/inventory 当 admission。该 map 发布时未编未跑，本岗尚未收到实际 admission DATA |
| 13 MCP_TOOLS | 同 11 的实际捕获 | 保持同一次 capture 的原生 custody，不能用 generic copy 偷换 |
| 14 MCP_RESOURCES | 同 11 的实际捕获 | 同上 |
| 15 ORIGINAL_MCP_CAPTURE_RECEIPT | 同 11 的实际捕获回执 | 实际 receipt；不是 SDK SourceIntent、continuation 或调用 ACK |
| 16 TRUSTED_EVENT_SOURCE_CONTEXT | Event：`RootEventSourceContextProducer` 新 typed preCore publisher | 同机 stateRoot/installed stockGameRoot、显式 null 外部历史与空 grants；实际 quote03 PASS，计划输出 342 B，无 issuer/CREATE/DataPin；不授 stock pristine 或 loaded 信用 |
| 17 LIFE_SETTINGS | Planner：`RootPlanningSettingsInputsProducer` | 实际 quote05 CORE_SETTINGS PASS，三槽计划输出 135/130/3515 B，不等待 20/21；仍保留 settings17 的合法 0B snapshot 语义。未 CREATE/DATA |
| 18 ADVANCE_TIMINGS | 同 17，沿原 Timings codec | 同次 CORE_SETTINGS QUOTE；真实 frames/ms，不猜默认预算，未 CREATE/DATA |
| 19 CAMPAIGN_DEADLINE | 同 17，沿 `CampaignDeadline` + 原 calendar | 同次 CORE_SETTINGS QUOTE；真实 Founding、date/raw 一致性保留，未 CREATE/DATA |
| 20 REMAINING_DOMAIN_SETTINGS | 同 17，读取配置引用的实际来源 | 保留 `stock_read` 必填可空语义、query-history 等真实来源闭包；前置 COA_READ_LIMITS quote06 已 PASS（119 B 计划），不是本槽 DATA，仍缺实际剩余来源闭包 |
| 21 NATIVE_DOMAIN_ORIGINALS | 同 17，逐 role 捕获真实 source pin | 只是 preGame 来源配置；不授 qualified cut、loaded 或 poststate 资格 |
| 22 PORTABLE_EVENT_EVIDENCE_MANIFEST | 原 `PortableEvidenceReader(ExactRef)` 固定历史 manifest | Event 本轮转述 Root 已明确选择下列现存原件；固定 1.19.0.6 离线历史证据合同，不要求本场第一帧，也不是本场 capture/grants。历史 P20 机器 unknown 不能追认为本场捕获 |

可选 `ROLLBACK_PROOF` 不计入以上 22 项。Ref 的 `RootFiniteFirstLiveRequestProducer` 产最外层 request，也不构成第 23 DATA。源码 map、codec、预期 hash、QUOTE 或 FileRef 构造器都不等于已创建 DATA。

Event 于本轮 21:47 UTC 只读观察、后转述 Root 明确选定的角色 22 原件为 `Z:/ck3_mod_rewrite/ck3_autonomous_player/src/xar_autoplayer/vanilla_events/portable_evidence/manifest_v1.json`，632294 B，SHA-256 `e87b1c86da8726ae3f9f1a3c375e70c9777f247b06ab8027f873474723637c50`。这个 fingerprint/stat 与 Root 的选择分别记录；299 blob 是原测试的源码断言，本轮没有因此读取或重新核验 299 个 blob，也未声称完整 reader 验收通过。

角色 16 的实际 raw Request 为 `D:/ck3-state/ck3-java-g2-robert1066-resume61/requests/event-source-context-quote01.json`，572 B、SHA-256 `83c7a01c8ea91f6d375acfb6bcfd700a9c975444f5d17fb27d6f4cf2edab2738`；Root03 → grouped request 的来源在 `resume61/event_registry/actual_request22/RAW-QUOTE-REQUEST22.json`（2265 B、SHA-256 `362680fcd1fe49256fd700a9e1c98185db4364d9915d3479cb46e720ae802c0f`）。这是请求原件而非角色 16 DATA；角色 22 历史 manifest 独立保留，不偷偷纳入本场空 grants。

五槽最新原始来源说明见[Planner 首发说明](../maintenance/2026-10-26-planning-settings-first-publisher.md)；MCP admission 两阶段及四 CLI 入口见[Public 首发说明](../maintenance/2026-10-26-public-mcp-firstlive-admission-bootstrap.md)。这些均为源码施工，不能据文档与预计输出构造实际 FileRef。

## 装载来源与 DATA 的关系

本轮只读复用了[当前 .4 feature reader 迁移来源](../ck3-native-ai/default-manifest-sentinel-migration-12004.md)，没有重复提取 EXE。实际 `ck3_12004_features.hpp/cpp` 与 `bridge.cpp` 调用链已区分于旧 `loaded_feature_manifest_v1` 的 1.19 叶：当前 .4 profile 指向 root `0x5CB87F8`、enum `0x47334D0..0x4733580`、runtime DLC set `0x5CC15E0`、name getter `0x3F4F8E0`，同帧读回仍由原共用 reader 执行。本轮没有运行此查询，也不借旧源码或历史 FIRST 给当前 runtime 资格。

该查询解决 effective gameplay feature flags 与 runtime `has_dlc` 集合，不能给出事件定义来自哪个 mod/VFS 文件、`replace_path` 是否生效或哪一行被解析成 loaded 节点。[direct-DDS 来源投影](../ck3-coat-of-arms-vfs-resource-provenance-mcp.md)也明确排除 engine resolver、definition merge 与 replace_path 语义，且其历史 R28/R30 绑定 1.19.0.6。故 16 的 stockGameRoot/evidence grants 是离线读取来源合同，21 是 Native 源码配置，22 是历史便携证据；三者均不应被 feature truth 或磁盘目录存在性升级成当前 loaded 定义来源。这个区分不新增首场必需角色或游戏第一帧前置。

## 能力 08/09 的源码链与实现

真实消费链已经核对：

```mermaid
flowchart LR
    R[明确的 Fresh startup Request] --> P[RootCapabilityInputsProducer]
    P --> C[实际目录身份与新 Driver 目标不存在]
    C --> G[原 RootBootstrapOutputGuard CREATE_NEW]
    G --> D[两个真实 DATA 原件与读回]
    D --> F[RootRuntimePreparedSources.frontend]
    F --> L[原 capability codecs 与 runtime lease 路径检查]
    L --> I[RootFrontendRuntime / InitialDriverBootstrap]
    I --> N[真实首个 Complete / Known]
    N --> M[原 initializeNewEpisode 守卫与 mint]
```

R5 `RootRuntimePreparedSources.frontend` 第 302–315 行读两个实际 DATA，沿现有 `DynamicCapabilities.decodeConfiguration`、`CapabilitySessionPresentation.decode/validateConfiguration` 并检查 state/SAVE/queue/Driver 路径属于原 runtime lease。`RootFrontendRuntime` 将它们交给原 `InitialDriverBootstrap`。真正 `DriverCapabilityStateProducer.initializeNewEpisode` 第 298–318 行只在真实首个 native/Driver observation 后运行，并要求空真实 gameplay history、尚未存在 cache、`restored=false`、`NEW_EPISODE`、`ACTIVE_NEW` 及无三项错误，随后才 mint 实际运行事实。候选不改变这些守卫。

本岗新 producer 使用有版本的强类型 Request，要求显式配置所有速度、布尔值和绝对规范路径；显式 Fresh 分支推导的会话参数仅供原初始化器消费。prepare 捕获 state、SAVE、queue 与 Driver 父目录的实际 Win32 身份，拒绝 reparse 路径、已存在的新 Driver 目标、异机、未来或过期请求，并在每次写入及读回前后复核。真正写入仍由原有限 Guard 与唯一 CheckpointFiles CREATE_NEW 执行；未知或部分写入不得重放。两个叶 JSON 通过原 codec 并规范排序，使独立 QUOTE/CREATE_NEW JVM 的字节稳定。

源码 map：`D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/formal_release/capability01/SOURCE-DELTA01.json`，5985 B，SHA-256 `85f88f7bd9959f581b10b788068ccf3b02bb4b5f87c5b126dd2909a40f1c7e4f`。只新增 producer/test 两个 target。共享 Kind/CLI 窄 hunk 由 Event 在 Ref77 的精确原件上统一接续，不回退 Family69、06/07 或 finite request 路由。

Event 的 `resume61/event_registry/source_context17/SOURCE-DELTA17.json`（10718 B、SHA-256 `da00d88703be3ab0aa49d2df9d5ec6b895bc1dbc593b0cee4abd083e136acfb5`）已封所需共享后继，并精确绑定本岗 map。本岗只读核对了两 shared 原件的实际字节/SHA 及 08/09 的 Kind、codec、DataRole 和 CLI 分派存在，未将该检查当 Java 类型检查。后继可能继续加入 Sway70，Host 须保留已合并窄 hunk。

实际 issuer 仅消费原 `RootBootstrapProtocol.Quote`。Event shared21 已把 capability 分支接入 `OrdinaryQuote`，phase 为 `CAPABILITY_INITIAL_CONFIGURATION`，authority 为 `AWAITING_REAL_INDEPENDENT_ISSUER_BINDING`，后继 shared23 保持此 ABI。本岗 test-only 后继 `capability02/SOURCE-DELTA02.json`（3242 B、SHA-256 `32490876eba94d30dd7ef10e6f4e673b203e749f1e9ceaf18f8799c7368d7393`）增加实际 pinned Request → shared main → stdout/LF → 原 Protocol.line 的回归，检查真实报价、目录和不写文件；不改 production01。测试源码已交 Host，尚未编译或执行。

原五个源码回归覆盖真实 pinned Request → 真实路径 → 原 Guard → 两原件 → 原叶 decoder 与 generic importer，以及错字段、缺必填 null、bool/float 混入整数、错误 binding 枚举、真实 Driver 文件出现、目录身份替换、原 request 漂移、QUOTE 不写、时效与异机拒绝。本岗本地检查仅包含字节/SHA 和 Java lexical delimiter；未另起 `javac`、Maven、JUnit、规定 CI 或 Game 执行。Host/Readiness 后续实际生产 CLI QUOTE 的结果见下文；它不代替 JUnit、CI、独立 issuer 或 CREATE。Host 继续独占复用 R5/m2 的增量编译与正式测试。

持久 CI 继续走原 `.github/workflows/static-ci.yml` 第 189–201 行的 Java full-reactor 入口。原 `ControlCi` 的 REACTOR_TEST_CLOSURE 调用 `ReactorTestClosure`，后者从实际 compiledSourcePins 收集标准 `*Test.java`，并拒绝失败、跳过或空的 Surefire suite；parent/local-service POM 未另设选择器。此测试类属于标准 `*Test`，须把 capability02 测试叶实际选入编译图，随后由既有默认 Surefire 和报告闭包验收；本次未增加共享 CI 分支，也未把该静态接线检查冒充 CI 已运行。

本岗新增 D 盘源码/metadata 限额 2 MiB、Z 盘独立文档限额 128 KiB，财务复核 `2026-10-26T08:00:00Z`；无重型子进程、旧卡重放、删除或释放预留。

## PROFILE_STAGING 实际上游与输出根冲突

首 PROFILE 报价先消费实际生产树和独立 manifest，由原 `FormalReleaseProducer.Request` 的 `PROFILE_STAGING/ISOLATED_PROFILE_IMPORT` 生成；不以 ENV、NativePlan 或 22 DATA 已存在为前置。此分支会通过原受管 `FormalReleaseGit.Session` 读实际 Git 来源，不要求发布模式的 clean/tag。

Root03 将 native stateRoot 选成 packageRoot，但该实际目录已有 `bootstrap-controls`、`environment`、`initial-data`、`requests`、`root-robert1066`。原 imported layout 固定生产树为 outputRoot/profile/mod-content/xar-production，manifest 为 outputRoot/xar-production.manifest.json；原 `Inputs.formalRelease` 以 outputRoot 为完整闭根且 retainedInputs=[]，`RootBootstrapAssetTree` 拒绝上述未声明目录。`FORMAL-ROOT-CONFLICT01.json`（2259 B、SHA-256 `52c352d44d268dfe2fa4efbaff21ccbea0b85d29066c54d5c1557abcca09ac63`）绑定实际 Root03、目录清单和三份生产源码。

Root04 已正式选 native stateRoot 为 packageRoot/native-runtime，profile/userdir 为其 profile 子目录；未移动原件或放宽 Guard。`ROOT-FIRSTLIVE-CONFIG04.json` 为 10660 B、SHA-256 `b2190d650b4380aeebfa6848c4772f02567243459abcba899b55006165c508ec`。全部 capability 输入逐字段与既有 quote02 相同，故 08/09 不重造请求。实际原 `PROFILE_STAGING/ISOLATED_PROFILE_IMPORT` 请求已写 `D:/ck3-state/ck3-java-g2-robert1066-resume61/requests/formal-release-producer01.json`（635 B、SHA-256 `e287f02359659f866c8953688a903834ccac2460f6061fc3e18666e72433aa4b`）。准备回执 `FORMAL-REQUEST-PREP01.json`（1840 B、SHA-256 `2d6a5d44a3608bdd4e833d240b0a42114d0b996406c0c6271a950bc6754bd348`）明确尚未 Java decode/QUOTE，实际生产树和 manifest 仍未生成。

原 Git 的三阶段八操作共 48 个 stdout/stderr 原件，最大 logical 为 3993600 B，须 Readiness/Capacity 为真实会话单独覆盖。`GIT-EXECUTABLE01.json`（751 B、SHA-256 `991f2aa680afc8da267b47d9c4c184a1724a0dbc9593bc278c94d226e6425bbf`）只读固定了当前 Git executable；尚未启动 Git 子进程、实际 QUOTE 或创建 production/manifest。

Readiness 已选原 Shared scope 为 packageRoot/bootstrap-controls/formal-release-session01、Session.controlRoot 为其 session、Git commandRoot 为其 git-captures；尚未抢建这些目录。原 source18 Session 限 Git Job 至 128 MiB、FORMAL deadline 至 20 分钟，外层 wrapper 的 review 必须等于实际 Session deadline；短时 wrapper/Execution 随 qualified SourceGraph 和 capacity fresh slot 生成，不能把财务 review `08:00Z` 直接当成长时 Session。执行入口为原 `RootProfileBootstrapSession run SESSION_PATH BYTES SHA BINDING_PATH BYTES SHA SHARED_SPEC_PATH`，不会直接重放旧 stdin runner。

Formal producer 的 prepare 无输出目录创建，Git.requireOutputRoot 只检查当前实体卷策略。为使原 AC/Guard 可实际观察 assetRoot，Readiness 按既有 Root8MiB 小目录授权于 `2026-10-25T22:44:31.184639Z` 仅 CREATE_NEW 空 native-runtime 根，entries=0；`readiness/bootstrap06/NATIVE-CLEAN-DIRECTORY03.json`（1299 B、SHA-256 `d2cb943424b8b9d61cfa54873d7f3d5ea10473551b044ed2694cac354ed77d86`）记录实际 Python stat。profile、manifest 和 Git scope 未建；此小目录观察不能代替后续 AC 的真实 Java NativeDirectory/census。

等待上游期间已补齐 [PROFILE/DLC 来源专题](../ck3-native-ai/prepared-profile-dlc-scope-resume61.md)：沿真实五 Asset → ENV → NativePlan prepared-profile 消费者核来源，区分空 disabled 列表、installed `.dlc` 清单、既有 actual4 runtime feature/script-DLC reader、账号授权与 VFS 逐定义来源。该支线由 Launcher 确认未重复，不改运行合同、不新增首场门槛，也不将源码审计称作已采集当前 loaded 样本。

## Root 已选配置与真实 QUOTE 请求

`ROOT-FIRSTLIVE-CONFIG02.json` 的实际原件为 7053 B、SHA-256 `1de9c1e7e13b655ef7074deac431f28eca66d4b520c30973f3df1a723383672d`，选定各 publisher 独立 closed root；不从共用 flat `initial-data` 执行 CREATE_NEW。08/09 同属 `D:/ck3-state/ck3-java-g2-robert1066-resume61/initial-data/capability`，目标为 `capability-configuration.json` 与 `capability-session-presentation.json`。

本岗实际创建的请求是 `D:/ck3-state/ck3-java-g2-robert1066-resume61/requests/capability-quote02.json`，935 B、SHA-256 `71fc2bf513437b82cd5e9ad757fdcf3c9faf021bb4da79ed577d2218653e64ee`，明确 `mode=QUOTE`、`binding_ref=null`、`FRESH_NEW_EPISODE`、速度 `1/1`、AB/canary 均 false，review `2026-10-26T08:00:00Z`；配置 state/SAVE/queue/Driver 路径来自 Root02。准备回执为 `resume61/formal_release/CAPABILITY-REQUEST-PREP02.json`（1535 B、SHA-256 `7271d8f2c86a0c18c3521bda31a79db45843b7f70cf523f2b218f8a2e8925df8`）。该原件已由 Readiness 沿原三参数 CLI 实际 decode/QUOTE；截至下述结果原件，**尚无两个 DATA 原件**，仍须独立 issuer/Guard 和 CREATE。

随后实际读回的 Root03 为 9741 B、SHA-256 `795b6982a4e294233efc05e6d882a2e9655b512531098c724d87936625403733`。本岗逐字段核对了全部 capability 输入，均与上述实际 Request 相同，故复用该原件而未重新生成。`CAPABILITY-CONFIG03-COMPATIBILITY01.json`（1359 B、SHA-256 `8af00801bfbdc241629dd763073ad7f807cf289076e9a4c7c2426f27c58d0c05`）保存当前选择、原请求与比较范围；新增 Native request/session/profile 值只属配置，不能升级为会话或 Game 事实。

### 实际生产 CLI 的 QUOTE 原件

Readiness 的 `D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/metadata/ACTUAL-QUOTE-RESULTS02.json` 为 17686 B、SHA-256 `d3cee9a1df7dbed17bd76d41d20b89794bb81025aa952fa4c7e1dfe6cd293afe`，观察于 `2026-10-26T05:45:43.747208Z`，machine_id 与本机一致。本岗已读回该原件并独立核对 capability 的 stdout/terminal 字节与摘要。七次实际子命令中，capability、event、sway、CORE_SETTINGS、COA_READ_LIMITS 五个 LF QUOTE 为 PASS；Family 的原路径错误和严格缺 `child_matrilineal` 的 retry 均保留 RED。这里未授独立 issuer、Declaration、Binding 或 DATA。

随后 `metadata/ACTUAL-QUOTE-RESULTS03-CLOSE.json`（同 executionroot）为 20788 B、SHA-256 `0f1fbf2671bf18eb4aa63fc6e41e78b9d91afee87932868202f979253876b0ab`，观察于 `2026-10-26T05:55:50.646128Z`。修正完整 snake_case 请求后，`readiness/quote08/stdout.log`（841 B、SHA-256 `809af0a4c9e812db26a951df42a8e5ad7b22e0f58798e2178ec1d09d21cd634a`）真实输出 `FAMILY_INITIAL_DATA`，三槽计划为 81/94/82 B。本岗已读回 close map 和该 stdout；当前八个实际子命令终态均 Job active 0，六个独立 QUOTE phase PASS、原 Family 两 RED 保留，合计 11 个计划输出、5846 B。这里仍是 DATA 0；DECLARE/CENSUS、FinancialRelease、独立 Binding 和 CREATE 尚未由该索引授予。

08/09 的实际 stdout 为 `D:/ck3-state/ck3-java-g2-robert1066-resume61/bootstrap-execution/quote01/readiness/quote02/stdout.log`，731 B、SHA-256 `32e54bfe93e066474b67668421cc1bae2c0a83f339688f607d80d765d9abf86f`。它是原 `xar.java-root-bootstrap-phase-quote/v1`，phase=`CAPABILITY_INITIAL_CONFIGURATION`、authority=`AWAITING_REAL_INDEPENDENT_ISSUER_BINDING`，asset_root 为原 capability 闭根；目录和 retained inputs 均为空。其两项是计划字节：

| 目标 | 计划 bytes | 计划 SHA-256 |
| --- | ---: | --- |
| `capability-configuration.json` | 339 | `b9d68ae2c197be2d1cd4772f7fe76872de79779f3cbdb08a640b5f30e5acba7d` |
| `capability-session-presentation.json` | 398 | `4a2bd2bb8e1b46a90b4532fcbe6ff4103744f96481800ea9dd4c1010f148d883` |

同目录 `terminal.json` 为 40091 B、SHA-256 `470d09bd107351303d79342b6631f99f97942cd8530b62fcdde03f94f35cd147`：实际 PASS、child exit 0、Job active 0、输入前后与 runtime 三项 MATCH，耗时 1.5347468 秒，Job 峰值 184627200 B / 上限 268435456 B。这证明实际生产 QUOTE 路由已运行，不是 JUnit/CI 或 Game 通过。计划 hash 不构成目标文件 FileRef；实际 CREATE/readback 前不得填 08/09 DATA。

CORE 三槽的 135/130/3515 B 与 CoA 的 119 B 同样只是计划。CoA 是角色 20 的既有来源前置，不增加第 23 个必需 DATA；五槽 aggregate 仍需 CoA 成品、NormalExit 三原件、query-history document 和同资格 v7 Native 来源。发行阶段复用结果索引 02 的实际 FileStandardInfo allocation 来源；索引 01 及其旧 allocation 值保留为历史，没有 grant 消费它。

本岗另于 `2026-10-25T22:12:43.451129Z` 直接调用 Win32 `CreateFileW`、`GetFileInformationByHandleEx(FileIdInfo/FileBasicInfo)` 和 `GetFinalPathNameByHandleW`，对 state、SAVE、queue、Driver 父目录及 installed game 目录作同句柄前后身份核对，driver-state.json 实际不存在。`DIRECTORY-CUSTODY01.json` 为 3001 B、SHA-256 `cae9689b420460b22a69e8d80aa9338f9e9f56fbc944efd03c4d6c3f6c662b0e`；这不是把 Root 的 Python stat 改名成 Java Witness，未来实际 producer 仍独立读取其 NativeDirectory。

新的共享 Steam 观察为 `STEAM-OFFLINE02.json`（2480 B、SHA-256 `77b91972e2b6dec11cdff732c9685d5a474147edaa4cdcdffd15f40e31cd9e53`，`2026-10-25T22:11:31.870292Z`，offline/true）与 `STEAM-EXECUTABLE01.json`（1306 B、SHA-256 `d07928e45478c3d9815a8b66d863034b8583e889c16481290a57da16f779a788`，`22:13:33.187314Z`）。后者从实际 Steam 进程路径完整读取 5823128 B 的 steam.exe，SHA-256 `f8a4ca44008c516eebecafaa4bc26772b2a6eb0fef8034bce56a3311e21ab705`、VS_FIXEDFILEINFO 版本 `11.15.70.27`，打开句柄前后 stat 及路径 stat 一致；M3 已读取复用。它只证明该时刻安装文件和后台状态，不代未来启动前的原新鲜度准入。
