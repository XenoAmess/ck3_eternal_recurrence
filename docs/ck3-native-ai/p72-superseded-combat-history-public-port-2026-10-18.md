# P72：新有效查询后摘要过期战斗研究历史

公共实现把旧 V2/V3 假设战斗查询的全文改为明确有损的历史摘要，避免每次规划与持久化继续复制已失效的大正文。触发条件是新查询已经通过原 typed normalizer、同帧检查、完整 canonical cache 发布及成功记录；当前最新 history 行、API 返回值和模型输入保留完整。该修改没有部署到当前 R8。

来源是 [P67 实际巨大回执和归档上限分析](p67-p68-combat-query-payload-and-archive-compression-2026-10-18.md)。本次没有重新读取 Driver、AUTO77 或旧 archive。机器 `xenoamess-full-tower-eb9d2c1186`；观察时间、外置 P72 来源和公共源码 pin 见[证据](evidence/p72-superseded-combat-history-public-port-2026-10-18.json)。它不能证明实际吞吐或 Driver 缩小比例，首30节点也尚未完成。

`combat_history_superseded_v1.py` 只处理同版本、更早 native revision、query sequence 更小的旧成功 available 记录，保留所有行、位置、index、command、ok、query frame 和其他结果字段。partial、unavailable、错误、同帧、其他版本和 battle-control 正文保持。general/siege 的完整预测输入来自当前帧 cache；active battle tracking 所需的 battle-control 历史、真实日进的 war progress、决策和 pending ledger 不改。冷恢复保留原行合同，过期缓存仍按原机制失效。

摘要保留场景、completeness、计数、规范 JSON SHA/字节和原查询帧，明确旧全文未保留、不可由摘要重建；本模块没有新 archive writer。没有已绑定原 MCP 路径时明确记为未知，不能声称原件已归档或能完整复原。已有闭场 Driver 和 MCP 原件不变。

每次最多摘要8行，单正文哈希上限64MiB，批次128MiB。哈希在原 history lock 外计算，提交前核对象身份，再显式失效增量 JSON 缓存。超预算或编码错误保留完整历史并返回原成功查询，不重发 Native；因此这不是无条件的尺寸上限。V2/V3 内部帧读取和 primitive 校验沿已有不携带 history 的路径，直接 snapshot 默认仍包含历史。

一次必要验证通过：21 tests、30 subtests，包含公共 Native 原 execute/primitive/normalizer/cache/record、Service typed API、合成持久化和恢复，以及 partial/unavailable、跨帧、digest 失败、缺缓存与重复摘要。端点是内存夹具，没有启动 SDK daemon、Native 或 Game；有限消费者源码审核沿已封 P72 记录，第三方历史正文消费者不在本次资格范围。未来 SDK 冻结和实机采用仍须独立绑定来源。
