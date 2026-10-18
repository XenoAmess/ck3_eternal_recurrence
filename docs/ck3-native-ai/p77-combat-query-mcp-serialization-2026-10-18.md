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
