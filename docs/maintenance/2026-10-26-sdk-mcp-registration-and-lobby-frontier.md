# SDK 原始注册、Java 准入与 Lobby 软件夹具的实际边界

`machine_id: xenoamess-full-tower-eb9d2c1186`。观察时间为 2026-10-25 21:44 UTC；文档日期按北京时间记为 2026-10-26。此记录为当前恢复工作提供精确来源与最小施工入口，不授予构建或实机资格。

原始 MCP 注册捕获与 Java 准入是两种产物。实际读取的不可变 `MEASUREMENT-REQUEST02.json` 位于 `D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume-current-20261024-r3/combat_contract/mcp_original01/`，大小 53,413 B，SHA-256 为 `19af91b87007676d9a4d2eb85cfb3046732f81c4ba07586026e9da8128d04a41`。其 `code_lines` 第 190–198 行只编码 catalog、tools、resources、registration_facts、inventory_proof，第 195 行明确声明 `ORIGINAL_REGISTRATION_FACTS_ONLY_NO_JAVA_ADMISSION`，第 226 行返回 `java_admission=NOT_PRODUCED`。该请求保留的是原始注册来源，不是首场 `MCP_ADMISSION` 原件。

当前 R5 `OriginalMcpCapture` 仍显式拒绝把原始注册报告当作 Java 准入。`RootPublicCatalogCodec.decode` 只反序列化既有 decision；`McpExecutableDirectory.assemble` 只消费既有 decision，缺实现时降级为 `UNMIGRATED`。本次对 R5 application/local-service 生产源码及历史 SDK closure 的有限搜索未发现初始 Java admission publisher；测试中的 `new McpCoverage.Decision` 不作生产结果。Public owner 正在补真实 pre-Core 生产路径。`RootRuntimeStartup` 第 84–89 行还要求实际 admission 的配置排除项绑定唯一当前配置原件，不能用全表 `UNMIGRATED` 代替。

另一个独立缺口是四软件包的五个 Lobby 原件。Native execution 与 M2 owner 均明确回复未持有真实 EXE 或五文件。已有唯一生产器是 Source60 的 `generic_gui_12004_fixture.cpp`，35,054 B，SHA-256 `1245fee9e45b10a2572e824cc9194d3f22cc64c4cc353d6cf757143570f5da0c`。其主函数只接收输出目录，运行生产 parser、mailbox 与 serializer 后输出十二个软件夹具文件，其中五个是：

- `lobby-callback-request.json`
- `lobby-callback.json`
- `lobby-callback-unavailable.json`
- `lobby-callback-bad-slot.json`
- `lobby-callback-bad-pin.json`

这五个原件由 `SdkFixtureProductionInputs` v2 消费，不能用 schema、源码或预计 FileRef 补齐。它们只验证受控内存的软件链，不证明已加载 Lobby、角色资格、随机抽取结果或 CK3 业务完成。

可复用研究图为 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/native10/build60/research`，对应 Source60，Release、`BUILD_TESTING=ON`。本次只读该目标的 Ninja link rule，去重后的 257 个直接文件依赖中 256 个已存在，逻辑大小合计 257,630,153 B；唯一缺少的是 fixture 自己的 object，目标 EXE 尚未存在。这只是文件存在性，未执行 dry run，不能承诺实际上只会重编一单元。

下一步沿现有受管 Native 入口，在新 S 修复 MSVC cleanup 并实际采用后，等待 Native owner 完成同图 cleanup 验证，再串行增量构建 `xar_ck3_generic_gui_12004_fixture`，以全新 D 盘隔离目录运行原生产器。具体来源、命令参数、128 MiB 初始峰值报价及资格范围记录在 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/sdk_execution/LOBBY-FIXTURE-INCREMENTAL-PLAN01.json`。未启动构建、fixture、SDK continuation 或游戏。此软件包缺口不增加为 Tools 编译、Java 直接首场或普通 Native production 的前置。
