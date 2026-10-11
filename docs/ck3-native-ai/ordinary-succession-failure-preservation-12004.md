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


## 2026-10-12：Endpoint关闭事实与原始异常

Endpoint沿原取消I/O与两秒join，线程仍alive时真实抛错并保留线程引用，不能清引用后声称driver关闭。启动ready超时或fatal先冻结原始启动RuntimeError，若关闭也失败，原错仍为顶层、关闭错保留为cause。MCP main若server.run已抛异常，driver.close失败作为note追加到原错；无原错时真实传播关闭失败。Runner既有cleanup追加与driver_closed标志保持，不新增join循环、transport、持盘或调用。SDK进程、Game退出与Endpoint关闭仍是独立事实。

本批07是完整采用，未同时套用旧04。Root初次采用已写完两个源文件，但回执父目录拼错导致记录失败；随后从31909b7e真实Git preimage重建三个hunk并逐字节核对现文件，只补回执，没有重套或再次改源。[实际采用回执](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-M7-ENDPOINT-PRIMARY-SOURCE-ADOPTION.json)。仍为source only，冻结SDK87/f9未改，未运行测试或继承实机重验。


## 2026-10-12：WorkerAdapter同次失败门诊断

R102 的首次继承人关系请求在原始回包中返回 `during_read_guard=snapshot_read_failed`，after仍为unknown。源码确认最终during读取走WorkerAdapter；缓存采样会先令epoch为0、锁外读取后再发布，但原回包没有指出具体失败门，不能据此归因采样窗口。

已采用两文件四hunk：actual4 WorkerAdapter每次沿原读取开始一次TLS诊断，在原cache、stamp、TLS、epoch、date、pause及exception短路处记录对应stage；现有during helper直接读取同次Fresh/Format。旧enum值保持，新增值仅追加。没有重读、重试、放宽守卫、替用旧缓存或伪造prefix；原失败请求不重发。实际失败门与根因仍unknown，M7 incomplete／自然跨代0。

[实际源码采用回执](D:/codex-ck3-background-spill/native71-continuation-20261010/runtime-01/native84-resume-20261012/ROOT-WORKER-FAILURE-STAGE08-SOURCE-ADOPTION.json)。冻结SDK87／Native86／R102未改，生产编译待新的实际SDK88 pin与Native87依赖闭包。15项源审与4项补丁复核完成；无测试、fixture或继承业务复验。
