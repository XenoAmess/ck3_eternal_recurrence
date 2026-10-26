# resume63：REA 框架与本轮执行方法

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26 UTC；`py tools/ck3_live_run_id.py machine` 在本轮重新读回同一 ID。本页先记录框架源审，实际 CK3 查询另记录终态，二者不互授资格。

## 来源与当前环境

复用 `D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01` 的 Node 24.22.1、REA 6.8.0、Rizin 0.9.1 与本地修补过的 Ghidra 12.1.4，不安装、升级或重导全 PE。发布源码 commit 为 `160d821ac9a0310afcb8d1fc427862dd6508add5`；历史 main commit 另记，不能混用。

14:36:17.728Z 重新读取 [sources.json](sources.json) 的 23 份引用，bytes/SHA 全部 MATCH。14:42:53.889Z 新读当前文件 CK3 EXE 为 101040248 B、SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`，11 个现用 Java runtime、工具 EXE、Shared 源码和 delivery 引用也全部 MATCH。版本名 1.20.0.4 / Steam 25734779 是其来源合同；文件身份不证明正在加载的游戏身份。

除已安装源码，阅读了同发布 commit 的官方 [native investigation](https://raw.githubusercontent.com/morluto/rea/160d821ac9a0310afcb8d1fc427862dd6508add5/docs/native-investigation.md) 和 [reverse engineering integrations](https://raw.githubusercontent.com/morluto/rea/160d821ac9a0310afcb8d1fc427862dd6508add5/docs/reverse-engineering-tools.md)。其能力说明仍须与本机实际结果区分。

## 框架分层

REA 把工具观察装入 Evidence，把支持、反证与剩余问题装入 Unknown registry，再提供保留、导入、导出及视图投影。provider 负责原始分析；REA 的 Evidence ID、schema 验证或 registry 结案不会自动证明 CK3 领域解释。

Evidence 的语义 ID 覆盖 subject digest、provider/profile、参数、raw/normalized result、confidence、authority、limitations、coverage 和链接。被选本地路径等展示元数据不参与这个 ID。ID 是公开算法的内容承诺，须另外绑定原 EXE 和原字节。`confidence=observed` 可以描述已观察的命令结果，其中仍可能包含解析错误。

Unknown 更新带 `expected_revision`，完整 bundle 合并先校验再原子提交。`verifyUnknownResolution` 只检查 registry 当前 status 与 resolution disposition：其 `truthVerified` 字段来自已存 `disposition=verified`，没有重新执行领域求证。八 M 研究记录仍须列支持、反证、待桥接条件和实际验证范围。

## 当前可直接采用的有限路径

**本机优先用 REA 的 Rizin 单次命令服务。** 已有同功能实测和完整退出证据；Ghidra 上轮 900 秒启动预算失败，没有成功 pseudo、native dossier 分页或 warm 资格。seed 在默认 auto-analysis 前运行，不能把全 PE 导入变成只分析 seed；本轮不重跑该路径。

正式 MCP 输入为：

```json
{"path":"原PE绝对路径","command":"有界Rizin命令","command_timeout_ms":30000}
```

CLI 为 `rea.mjs execute-rizin-command PE COMMAND --command-timeout-ms 30000 --json`。官方共享服务是 `createReverseEngineeringService(environment).executeRizinCommand(input)`，使用它仍须执行 `close()`。首次 Java producer 生成 argv 后，Shared 在 child 前拒绝；Root 随后授权直接调用已安装官方共享服务，实际命令与调用代码封在各 case 的 invocation/receipt 中。没有新增 runner 或修改框架源码；direct 成功不授 Shared 资格。

已实测有效的命令形状如下，VA 和范围按每题固定：

```text
e analysis.limits=true; e analysis.in=range;
e analysis.from=VA_BEGIN; e analysis.to=VA_END;
e analysis.calls=false; e analysis.hasnext=false;
e analysis.jmp.after=false; af @ VA_BEGIN;
afij @ VA_BEGIN; pdfj @ VA_BEGIN; agf json @ VA_BEGIN
```

这里只限制所请求的函数分析和跟随范围，Rizin 仍加载原 PE。`pdfj` 字节、指令边界、分支目标和 `agf json` 图要与独立原件核对。旧 `agfj`/`pdc` 失败不能因 exit 0 算成功；本轮不依赖它们。空 xref 只描述实际已分析范围，不证明全程序没有 caller。

raw 输入只有 path/command/timeout，没有 detail、fields、offset 或 limit。输出上限为 stdout+stderr 共 16 MiB，超限及不完整 UTF-8 明记；文本 capture 不是原始字节 archive。timeout 分别用于前置 stat/digest 和命令，不是整个工作包统一墙钟。命令前后 SHA 相同不能证明执行期间每一瞬间读取相同字节。

## 成功 native provider 的语义路径

以下为源审已支持、此机尚未成功的路线，不因示例存在授执行成功：

```json
{"procedure":"0x141d64290","detail":"summary"}
```

`analyze_function` 先完成完整 dossier，再保留 parent 并返回 summary。后续取 `normalized_result.parent_evidence_id`，不能用 summary 自己的 Evidence ID 冒 parent：

```json
{"source":{"kind":"retained-evidence","evidence_id":"ev_完整parent"},"view":{"kind":"native","facet":"basic_blocks","offset":0,"limit":64}}
```

可选 facet 包括 procedure、pseudocode、assembly、basic_blocks、callers/callees、incoming/outgoing references、unresolved_calls、strings/names、native_api 和 value flow。行类按原数组分页；pseudo 按 UTF-16 code units，必须跟实际 `coverage.next_offset`，不能按请求 limit 自加。`N/N` 只证明此 view 已读完；provider 声明 unavailable、未知 count 或 discovery 未完成仍保留未知。

Rizin raw Evidence 不是 `analyze_function` dossier，不能据它调用 native facet，或手工改 operation 让投影通过。地址保留 `0x` 字符串；VA/RVA 算术用 BigInt，64 位文件身份和时间用规范十进制字符串。

其他接口也先按 provider 与覆盖范围使用：`read_bytes({address,length,document?})` 默认256 B，本轮调用方必须自行设小界限；`read_function_instructions({procedure,document?})` 返回 provider 指令；`inspect_native_instruction({address,document?})` 与 `resolve_containing_procedure` 不把邻近地址猜成包含关系。`procedure_callers/callees` 只列已解析静态直接边；`procedure_references({procedure,direction:"incoming"|"outgoing",document?})` 是原始引用，不能把空集解释为整个 PE 无 caller。

Ghidra 的 `search_bytes({pattern,mask?,start?,end?,limit?,cursor?,document?})` 默认 limit100、允许1..1000，范围端点 inclusive、不跨 memory block，续页跟 `next_cursor`。这些合同来自已安装 `dist/contracts/hopperMemoryContracts.js` 与工具 catalog；本机没有成功 native provider 观察，接口源审不能冒实际分页、xref 或字节查询通过。

## 保留、持久化与关闭

完整 parent 在 close 前经 `export_evidence_bundle` 写入新文件，并保存 bundle bytes/SHA、parent ID、PE SHA/profile。普通 close 会清 session records/cache；裸 ID 和临时 Ghidra DB 都不是永久 locator。MCP import 可合并进会话；CLI import 只校验文件并返回 counts。上一轮 Node-only import/export 已通过，仅证明那份历史 Evidence 的保留与恢复。

Windows owned process 只有主退出、stdout/stderr 都结束、`activeProcesses=0` 后才释放 handle，`process_close` 完成才发 close。kill ACK、主退出或工具 success 不能代 Job0。cleanup 未确认时继续原 owner 的 close，不重新提交同一查询。关闭结果与 payload、证据解释、游戏业务后态分别记录。

初始两串行 child 计划沿 `SourceGraphCommandSpecProducer` → exact BINDING/SPEC/INVOCATION → `SharedOwnedCommand`；真实结果是 Shared 在首 child 前拒绝，见[入口记录](resume63-callee1d64290-entry-result.md)。后续官方 direct 路线仍按新鲜容量、内存、期限和固定范围执行。Rizin 的原装 WindowsOwnedProcess 完整 close 已观察；外层 exec 的联合峰值与 Job0 为 NOT_MEASURED，不把受控 provider 的退出冒外层资格。第二题 decoder 也复用原装 owned-process 入口，第一题 plain-spawn decoder 峰值未量测。

## resume63 问题与实际结果

Root 选定 `0x1D64290..0x1D64376`，230 B。问题为：caller `1A20056` 的 root/candidate gate 使用哪些输入、返回 AL 走哪些路径、读取哪些内存，以及该范围的正常局部 CFG 是否闭合。历史 RF metadata 给 unwind `0x51E6AC0`，其采集机器未知；本轮不会把它倒填为本机新观察。

本轮 [PLAN01.json](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/resume63-callee1d64290-01/PLAN01.json>) 为 5203 B、SHA `d2cc71efd1e4d3d08edd148dae0920dc567d2e58240ad35271cf5542a5311d99`。独立 RF 解码后只运行一次有界 REA/Rizin；不跟 callee、不读取 global data、不复制 PE、不启动 CK3。原件由唯一 backend owner 提供，八 M 共享解释和精确引用。

上述为初始问题定义，后续已取得两份新的有限原件：`1D64290` 230 B/48条/5块6边，及独立新题 `24C5260` 119 B/35条/4块4边；均鲜读当前 PE 的 RF，Capstone、Rizin、原始相对跳转算术与局部 CFG 一致。M5 对两题独立复核；第二题闭场时仍是 PENDING，15:27:58.546Z 另建独审原件，不修改旧 close。完整数据流、成本和引用见[实验记录 resume63 段](experiments.md#resume63两次新增有限查询)。

第一题保留 `372DF10` 返回的原始低 byte；第二题仅 AL 归一化，且 iterator call 前后的 end 是两次读取。opaque callee、副作用、异常与 unwind 均未闭合。`+0x308` 仍仅为 caller 的未知数值累计来源，兵力、参战、到场、胜率与实机资格均未由本题建立。当前没有整体提速或模型 token 收益结论。下一题先复用已持 `28BFCD0`、`A11F60` 原件/源码，再由 Root 选择最小未闭的 `2B9D260` 边界问题；本页不授新采样。

## 精确源码导航

相对 `tools01/rea/package/`：

| 主题 | 源码位置 |
| --- | --- |
| Evidence 合同/ID | `dist/domain/evidence.js:95–132,174–198` |
| Evidence/Unknown owner | `dist/application/investigation/InvestigationRecords.js:3–66`；`EvidenceLedger.js:18–135,260–274` |
| raw schema/参数 | `dist/domain/reverseEngineering.js:4–15,59–69`；`dist/rizin/RizinCommand.js:8–16` |
| raw pre/post、输出、close | `dist/application/reverse/ReverseEngineeringService.js:48–105,134–144,178–266,416–566,609–721` |
| 现有 CLI | `dist/cli/reverseEngineeringCommands.js:15–49,158–178` |
| native retain/分页 | `dist/server/registerEnhancedTools.js:152–193`；`dist/application/analysisView/AnalysisViewService.js:145–164`；`dist/domain/analysisView/analysisView.js:115–141`；`nativeFunctionView.js:145–225` |
| Ghidra 全 import/seed | `dist/ghidra/GhidraLauncher.js:446–578`；`bridge/ghidra/ReaGhidraAnalysisOptions.java:29–80` |
| Windows cleanup | `dist/windows/WindowsOwnedProcess.js:328–391`；`dist/ghidra/GhidraRequestQueue.js:74–118` |

Shared 冻结源根为 `D:/codex-ck3-background/ck3-java-tools-s26-source-r4-resume61/tools/src/main/java/org/xar/ck3/control/build/`：`SourceGraphCommandSpecProducer.java:159–182,411–432` 生成现有机械入口；`SharedOwnedCommand.java:285–290,389–465` 校验并执行。runtime/source 是历史完整包基线；本轮 fresh standing 只固定新资源约束，实际 Shared 前置拒绝，不能据此授入口通过。
