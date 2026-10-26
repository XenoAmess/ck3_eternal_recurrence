# REA 工具与 CK3 研究路线

2026-10-26，machine_id=`xenoamess-full-tower-eb9d2c1186`，rea-agents 6.8.0。默认 **SOURCE_ONLY**；r13单卡执行。发布来源见[sources.json](sources.json)，包未报gitHead；源码不授backend/Game/token验收。

## 先选实际可用的入口

| 入口 | 源码支持 | 当前资格与拒绝边界 |
| --- | --- | --- |
| analyze_function | 已选 Hopper/Ghidra/IDA/Kuna provider 的 capability→同 client | 不支持则typed error，不换engine。auto仅1候选绑定，多候选拒；open/health不授函数分析。 |
| inspect_analysis_view | 校验既有Evidence后投影，不重新分析 | native parent须artifact-bound analyze_function；Rizin command连view summary也无projector。 |
| execute_rizin_command | 独立 Rizin CLI，不是 deep provider | 已有历史 raw 实测；它不授 native facets。启动失败无 backend fallback。 |

此机Ghidra cold03超时，无伪代码/native page/warm验收；其余native provider仅发布接线候选。实测见[实验](experiments.md)、[学习记录](learning-log.md)。

## 后续有限执行路线

1. 固定原PE SHA/build、image base、范围、provider/profile及问题；已有字节先复用，局部CFG可选Rizin。
2. native provider实际就绪才用`analyze_function({procedure,detail:"summary"})`。先计算并retained完整dossier，无retention拒绝，不能造parent。
3. 取`normalized_result.parent_evidence_id`，summary自ID不是parent。用retained-evidence source与native facet的offset/limit取小页。
4. 各页核同parent/原件/函数/facet，保availability/coverage/truncation/unknowns；再核原字节、caller/receiver/写入/consumer；close前export完整Evidence。

## 五题形成的可靠性边界

| 题目 | 研究结论与 CK3 用法 |
| --- | --- |
| 分析范围/复用 | Ghidra 当前路径固定 import/readOnly/deleteProject，seed 在默认 auto-analysis 前运行，不是函数范围或 no-analysis 开关。disable 名单只对 registered analyzer 设 false；不适用项单报。可复用成功的同活动 client，失败启动不授 warm cache。 |
| session/cache 身份 | session比路径/sourcePath，cache比内容SHA+provider/profile。正常open校新target；active cache可直接回旧SHA，外部换PE不自动可见。失败open可恢复旧target但仍返回原failure；CLI replay先resolveTarget。切版核实际open/fullSHA，不只路径/health。 |
| 分页/覆盖 | native默认offset0/limit64；pseudocode按UTF16 units，surrogate可缩页，须用实际next_offset；row facets按原数组分页。exhausted/N/N仅本view；unavailable可为状态项，counts=null/discovery unknown不变。limitations可能限幅，查parent。 |
| 地址精度 | 地址string→BigInt→hex；Java unsigned long→BigInteger→string并回验space offset，拒截断。VA/RVA用BigInt、API用0x string/space并核selection；未解析hex可走file-offset fallback。file_offset/source_index非任意uint64/FileID，JSON不修复Number舍入。 |
| timeout/cancel/close | 单函数remote timeout可保session；queued Abort只撤队，active Abort才await cleanup，closePromise保首个close参数。Wire settle/kill ACK/主exit不授Job0；还需双stream结束+active0+process_close。poll error不必结束Promise。cleanup unknown只继续原owner close，不重发操作/Game动作。 |

## Evidence 的保留与输出

普通close默认清records/cache；裸parent ID非磁盘locator，DB/snapshot不代Evidence bundle。CLI函数`detail=summary`需新`evidence_output`先存完整parent；raw无此delivery组。`--filter-output`只显示、不保原件。

MCP import可入session，CLI import只校验回counts。schema/ID/manifest/unknown图自洽非provider实跑/外部PE证明；改semantic数据保旧ID拒，公开算法重算新ID不是签名。保bundle bytes/SHA+parent/EXE/profile。

**真实Node-only复用**：[EvidenceReuse01](</D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01/cases/evidence-reuse01/READBACK01.json>)已验证历史record导入→complete/summary→export→close后文件仍在，值/类型/ID/params/null profile未变。serialized CallToolResult为131281/2183B；摘要无CFG/操作数，不能答原ADD问题，非同质量/token节省。无新PE/provider，也未证明raw自动留存或native parent跨进程恢复。

`rawResult:null`只省重复raw；bundle默认complete，filters仅summary，0匹配非未保留。

## Rizin raw 与“完成”

只有 path、command、command_timeout_ms；无 detail/fields/offset/limit。timeout 默认120000ms，范围1..2147483647，按 phase；stdout+stderr共享16MiB原Buffer cap，跨chunk合并后解码。截断UTF8可替换并留limitation；文本Evidence非raw字节archive，须保truncation/unknown completion。它会关闭活动session；命令/插件外部输入不自动绑定Evidence，前后SHA不证明调用中每一刻的字节。

exit0/complete、MCP success体省略 isError，均不认证命令语义。既有 CLI 真例 raw.stderr 含 parser error 而 stdout空；新106B case也有外跳图 stub/error，同时局部29指令独核全同，逻辑续边仍UNKNOWN。查 [学习记录](learning-log.md) 的原件。非零退出也可为observed result；typed error可能附 partial observation ID。保 stdout/stderr/exit/signal/truncation/UTF8 limitations，按具体命令正向核形状、地址、条数与原字节，不能用任意错误 regex 作通用门。

## 工具上下文与费用

`REA_MCP_INPUT_SCHEMA_PROFILE=compact` 默认，full可选；两者仍广告全部229工具。68个 compact input 是 reduced 结构，客户端看不到全部嵌套约束，服务器仍 canonical 校验。13KiB 是单工具广告预算。`REA_MCP_OUTPUT_SCHEMA_PROFILE=off` 只移除 outputSchema，保完整结果验证/structuredContent；它还让默认 stdio 走 eager 而非 deferred，不能称无代价省上下文。

deferred只延迟runtime，不延迟广告；REA server无task allowlist/namespace配置。setup可保Codex enabled_tools/disabled_tools；当前host实效未核。catalog 文件 SHA、tools数组指纹、REA catalogIdentity 分开；缓存须绑实际 profile/identity，不只版本字符串。cold03仅保存 count229＋3个 selected advertised schemas及聚合指纹，不是完整229 runtime schema原包。

两旧样本REA内部raw/normalized重复；输出为direct的2.62/2.28倍，非普遍比率，direct正文含测时差异。MCP成功result同时带text/structuredContent，源码预算计两份；非最终JSONRPC全帧证明。bytes≠token。REA_MCP_MAX_RESPONSE_BYTES最小/默认10MiB仅接收保护。A/B固定问题、PE/profile、parent与事实质量，计全部上下文/tool/请求/页/重试/答案，分报排队/准备/payload/验证/关闭；token用actual usage或注明模型/tokenizer计量，当前收益未测。

## 精确源码导航

`T=D:/ck3-state/ck3-java-g2-rea-eval-resume62/tools01`，`P=T/rea/package`。下列以`D=dist`、`B=D/application/binary`、`V=D/domain/analysisView`、`G=D/ghidra`为相对P路径：

- 五题：`G/GhidraLauncher.js:446–578`、`bridge/ghidra/ReaGhidraAnalysisOptions.java:29–80`；`B/BinarySession.js:646–650/771–788/959–975`；`V/analysisViewText.js:7–28`；`bridge/ghidra/ReaGhidraBridge.java:4534–4546/4597–4623`；`G/GhidraRequestQueue.js:60–127`、`D/windows/WindowsOwnedProcess.js:315–391`。
- 保留/输出：`D/cli/analysisEvidenceDelivery.js:28–35/83–134`、`B/BinarySessionRecords.js:204–208`、`D/application/reverse/ReverseEngineeringService.js:536–555/609–648`。
- 广告：`D/config/mcpInputSchemaProfile.js:9–32`、`D/config/mcpOutputSchemaProfile.js:4–20`、`D/server/DeferredEvidenceMcpServer.js:31–79/109–117`、`D/application/ClientRegistration.js:38–64/144–208`；实际bundle已由owner只读交叉。

完整FileRefs见sources/experiments/learning。基线审计SHA256`6802617f069579f33c06e89bf548d55dac6aa55abe4ce478be15d99f4adf3f94`。独立为r40①–④具名片段、r02⑤三关系、r38复用逐值/质量核；其余owner源审。无Game/token验收。
