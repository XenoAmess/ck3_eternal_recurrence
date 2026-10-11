# 普通自然继承失败保全（CK3 1.20.0.4）

2026-10-12：两项源码修复已采用，状态 `SOURCE_ADOPTED_NOT_RUN`。冻结 SDK87/f9 与 Native86 没有这些增量；没有运行测试、fixture、FIRST 或自然继承验收。M7 仍 incomplete，实际自然跨代仍为 0。

## Close 提交 ACK 与回收失败

原生完成 modal Close 后，原 ACK 可能被 mailbox reclaim 失败的统一错误覆盖。现在只保留实际生成的 ACK JSON 字符串，追加 `death_succession_close_failure_v1`；外层仍 `ok=false`，材料验证仍 false。不新增查询，不重新提交 Close，不推进日期，也不以 ACK 替代继承结果。

Python transport 保留原请求、原错误 frame 与提交前最后已知快照，核对 command/request/protocol、reclaim 阶段及原 ACK 的严格整数、身份和完成字段。只有原 ACK 验证成功才返回 `submitted_unconfirmed`；不合格保持 `submission_unknown/accepted=None`。两条分支都无 post-query、Continue 或 SAVE，不把最后已知 before 当作新的 ending frame。

## Continue 已应用但 Driver 持盘失败

`_record_command` 沿用原来的一次 `_persist_driver_state`，仅在实际成功的 `continue-as-reconciled-successor` 记录当次失败。编码前在原锁内冻结 episode、goal、lifecycle、pipe/PID 绑定；保留逻辑 `continued/accepted=true`，追加持久性 `unconfirmed` 与实际异常。它不读取旧 Driver 或重复持盘。

`ck3_auto_turn` 返回 `is_error=true`，同时保留 `original_turn` 与持盘失败诊断，明确已经应用的 Continue 不可重发。现有 `native_auto_run` 在 Close/SAVE 前停下并保留原结果。失败专用标志阻止随后的 `driver.close()` 再次 flush 该失败；observer 仍 dispose、endpoint 仍 close，dirty/error 与新 episode/goal 留在内存。后续显式持盘成功才清除此标志。

直接调用 `ck3_execute_step` 的既有接口仍返回追加诊断的结果，调用者须检查该诊断。当前 Root 使用的文件队列 `ck3_auto_turn` 路径先拒绝 `is_error` 并保留原 outbox，不产生 successor SAVE 或新信用。历史失败不据此回填原因。

## 源码与交付

涉及 `native_bridge/src/bridge.cpp`、`death_succession_modal_private_transport.py`、`native_driver.py`、`mcp_server.py` 和 `native_auto_run.py`。Native Close 增量需要后继 Bridge producer 与 DLL 重链；Python 与原生须按实际构建版本分别登记。

候选经过 15 项独立源码审阅及定向修订复核。Root 逐 hunk 核对唯一精确 preimage，保留源文件 CRLF/LF 后采用；没有用宽松 token 匹配或项目导入预演。回执：[源码采用](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-M7-EXACT-NORMALIZED-SOURCE-ADOPTION.json)。原 4 GiB 来源范围与 `2026-10-12T16:47:28.264315Z` 期限不续。


## 2026-10-12：Root章节结果来源明确化

普通循环结果的`current_episode`保持原last verified transition/controller adopted snapshot语义，新增明确来源字段；循环异常后`live_episode_after_error=unverified`，不以错误中的旧章节字段声称当前实机章节已验证。原outbox失败与pending请求保留，不解析错误结果来增加天数、继承次数或SAVE信用。源码采用回执为外置`ROOT-EPISODE-PROVENANCE-SOURCE-ADOPTION.json`；没有新增执行调用。


## 2026-10-12：持盘失败的后续消费者保全

Service在确切`executed`、successor `accepted/continued`且当次持盘诊断`failed`时，在Sway/Feast后续快照或查询之前原样返回outcome；既有MCP错误回包可保留完整`original_turn`。Runner在收到实际result的首个副本时冻结`original_result`，first-failure也保留它，避免后置只读异常先丢失已经应用的Continue事实。没有新请求、重发、额外持盘或信用；原章节验证和失败停止门禁保持。回执：[源码采用](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-M7-ORIGINAL-RESULT-SOURCE-ADOPTION.json)。当前SDK87仍未含此批新源。
