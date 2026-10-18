# P77：保全战斗查询 AUTO 的完整结构化结果，减少重复文本

公共 `ck3_auto_turn` 对成功执行 V2/V3 研究查询的包，显式返回完整原 payload 到 `structuredContent`，文本只放查询状态、帧及完整结果位置。Service、Native、canonical DTO、风险判断和全部原生字段不改；当前 R9 没有采用本修改。

依据 [P67 的封口结构诊断](p67-p68-combat-query-payload-and-archive-compression-2026-10-18.md)，AUTO77 原件100,646,305B，其中完整文本75,645,309B，结构化结果25,000,533B。这里仅转引已封小元数据，没有重新读取该回执、Driver 或旧 archive。87.814秒是外层调用至客户端 `model_dump` 的总时间，不包括随后队列的字节计数编码和原子文件写入；不能把它全部算作 Native CPU 或本补丁可节省时间。

本机 MCP2.0 的 `FuncMetadata.convert_result` 对普通字典先调用 `_convert_to_content`，以 `pydantic_core.to_json(indent=2)` 编码整份文本，再执行 output-model validation 和 JSON `model_dump` 生成结构化副本。显式 `CallToolResult` 沿 SDK 原分支仍执行同一个 output-model validation，随后直接返回，省去上述整份文本编码及 output-model JSON dump。最终结构化结果的传输编码、客户端解码/校验、Native 采集、normalizer、cache、归档和队列持久化仍存在。

真实注册 MCP server＋官方 `Client(server)` 内存往返的合成小 DTO 验证通过，包含 `ck3_auto_turn` 包裹 V2/V3 查询，并非只验证 direct-query tool。V2完整结果21,419→5,548B，V3为22,354→5,564B；完整文本15,229/16,144B变为383B摘要。两者的原始完整 structured 值保持相等；实际 SDK 全文本转换1→0、output-model JSON dump 1→0、output-model validation 仍1→1，错误结构化根类型仍被原校验器拒绝。三个测试通过，未做大型 benchmark 或87秒同帧A/B。机器 `xenoamess-full-tower-eb9d2c1186`、时间、精确源码和回执见[证据](evidence/p77-combat-query-mcp-serialization-2026-10-18.json)。

消费者边界如下。

| 消费者 | 合同 |
| --- | --- |
| Root queue／classifier优先读取 structured content | 完整 payload 和所有校验字段保持；该结论是源码与合成资格，当前 R9 不变 |
| 只读取 AUTO 的 `content[].text` 的客户端 | 现在收到事实摘要，必须取 `structuredContent` 才有完整数据；文本不再是可还原全文的 JSON |
| Service／Native／模型直接 API | 原值和完整正文保持 |
| direct query tools、`ck3_execute_step`、非查询／blocked／不一致 AUTO、原错误通道 | 保持原转换；本次没有优化这些路径 |

Native25 冻结 bridge 对一次 query 只构造一个完整 `combat_simulation_inputs` JSON，内部 knight capture 仍完整附入。公共 serializer 返回一个完整临时字符串再追加到外层 buffer，后续冷构建可考虑直接 append/stream 以少一个临时大字符串拷贝；不改变字段，也不减少 wire 字节。两份不同采样阶段的 capture 不能仅因大小相同而共享或省略。跨 JSON 路径 intern/ref 若要减少 wire 重复，需要新 Native 协议和解码合同，本次不施工。原 normalizer 的 detached-copy 合同也继续保留。

后续最小测量面是分开记录 Native read/serialize/write、Python pipe decode、normalize/cache/archive、MCP shaping、client decode/model_dump 与 queue encode/write。现有87秒证据没有这些分项，不能估算墙钟收益。首30尚未完成，本工作不停止有效长局，也不要求为它轮换 SDK。

2026-10-18 后续补充：已结束的 R9 响应349..744固定窗口，实际时间为01:12:03.420044Z至01:23:51.773315Z，708.353秒推进271日，即 **2.614秒/游戏日**。机器仍为 `xenoamess-full-tower-eb9d2c1186`，统计于01:28:51.495410Z；来源是已封小 MET、TURN、计划和最多8192B的 AUTO 头部，不解析大 AUTO 正文，也不读取 Driver。396份响应合计157,497,002B，其中46次市场查询149,754,146B，占 **95.08%字节**，但调用时间45.823秒仅占 **6.47%总墙钟**。46次驻守承担全部271日、耗375.428秒，占53.00%墙钟；46次军力查询未发现相同帧重复。188轮有142轮零日，其中141轮只读查询、1轮事件选项。143.016秒调用间空档含最初77.896秒未知空档，保留在统计内，没有归因到 Native CPU。此窗没有战斗输入研究查询，不能用此前 combat MCP 小样本比例解释这段吞吐；也没有同状态优化前后 A/B。

针对该窗口主要的回包字节来源，另备最窄的市场 AUTO 候选：[独立 MCP shaping helper](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mercenary_query_mcp_result.py) 只处理 `ck3_auto_turn` 成功、available、原生、只读且 outer／plan／result 步骤均一致的 `query-player-mercenary-context-v1`。完整原 payload 保留在 `structuredContent`，文本给出公司数、来源帧和完整结果位置。Service、Native、市场 normalizer、采购决策、价格、雇佣、cache、history 与 pending ledger 均不改；direct market MCP、unavailable、错误、hire 及其他 AUTO 仍走原转换。仅依赖成功 AUTO 文本全文的客户端需要改读 `structuredContent`。

[市场测试](../../ck3_autonomous_player/tests/unit/test_mercenary_query_mcp_result.py) 在实际 Python Driver／Service 查询路径接内存 endpoint，再经真实注册 MCP 和官方 Client 往返；AUTO 规划包由合成 Service seam 提供。4项测试于01:47:14.435805Z通过。标准 JSON 字节再次解码后，完整 structured 相等，signed64资源成本、公司ID0与`0xffffffff`、employer的0／null区别、允许债务时`can_afford=false`而`can_hire=true`、query sequence及来源帧保持；现有 consumer 仍拒绝过期身份与公司 composition 错绑。输出 schema 继续校验一次，非法结构根仍拒绝。该小样本完整回包16,088→6,468B，文本9,323→433B；避免一次全文 pretty encode 和一次 output-model JSON dump，保留完整结构化编码、Client 解码及业务校验。

此市场候选及新增 CI 测试条目仍待 Root 审阅，未提交、部署或纳入当前 R9／SDK04；没有新的性能实机提升结论。45.823秒包含规划、Native 等待、normalizer、传输和客户端工作，能节省多少尚未知，不能把95.08%的字节占比视为同等墙钟收益。新增资格回执、固定窗口精确摘要 SHA 和来源见同一[证据文件的追加项](evidence/p77-combat-query-mcp-serialization-2026-10-18.json)；这些材料也不证明首30已完成。
