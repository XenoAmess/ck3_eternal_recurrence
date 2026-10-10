# R42：已缓存启动事件是 `.20`，completed marker 属于后继 `.2`

既有 R34 D2a、D2b 和 R38 selection 后的 JSON 都保存 actor31254 完整 `alive_data.variables` AST，三份各103个变量。`lyd_factory_diag_empty_transaction_completed` 在这三个原始变量节点及完整缓存包中均不存在。此次只读已有 JSON，没有重新读取91MB存档正文；完整缓存包和 seed 继续外置，只保存变量精确片段及其来源 pin。

R34 D2a 的原 SDK/native event 回执和 R38 重新载入后的原回执均确认 namespace `lyd_factory_diag`、definition `.20`、instance121、root31254、date53144712，native option0 显示且可用。两轮 calculatedEventId/运行目录序号不同，不用它们替代 definition/instance 身份。Source03 的 C4 prepared 合同准确等待 `.20`，并绑定同一 D2a seed：91,711,686字节，SHA-256 `a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c`。

旧 R38 与当前 overlay 的 `.20` 源块（事件文件52–77行）逐字相同。它的 event/option guard 只含 stage20 与 unheld-title，不检查 completed marker。选择该 option 后，73行才调用 D2 effect；当前 effect121行写 marker、123行触发后继 `.2`，`.2` 的87/94行才读取 marker。这一阶段关系不支持把 seed 中 marker 缺失当作启动故障或据此修改夹具。

Source03 host 在稳定 native owner/map frame 和 campaign-root 查询之后，820行才调用 saved-startup admission。产品 `admit_saved_startup_event`（195–201行）只核 `.20` 身份，返回 `business_pass=false`，不选择选项、不检查 marker。handler24389字节、SHA-256 `f2fbbfc3c78d7cfe7d45b5c2d0afd0337dd9ebd834f7c81ce46c672dfff49964`；依赖 case JSON3257字节、SHA-256 `fd3ebf58bd01cb2998a47c5f9faa0225d478692134b2185510074b3c0cba0955`。R42 的未注入加载超时尚未进入这个 typed handler；实际失败见[独立 R42 RED 报告](2026-10-10-r42-shared-runtime-startup-red.md)。

全局保存事件队列不在这三份角色/title缓存内。只查本轮、R41加载诊断、R42 RED及 saved-startup admission 四个既有 INDEX，其元数据没有标识 event-manager/saved-queue 离线投影；这不是对全盘文件的不存在声明。加载停在 powerful vassals 的原因仍 UNKNOWN，未以 marker 缺失归因，未更改夹具或安排新启动。若继续选择保存事件恢复方向，须另行明确一次有界队列投影的输入与范围，本包没有执行它。

永久证据：[INDEX.json](acceptance/2026-10-10-r42-cached-startup-event-facts/INDEX.json)、[VALIDATION.actual.json](acceptance/2026-10-10-r42-cached-startup-event-facts/VALIDATION.actual.json)、[RAW-EVIDENCE.zip](acceptance/2026-10-10-r42-cached-startup-event-facts/RAW-EVIDENCE.zip)及[归档生产器](acceptance/2026-10-10-r42-cached-startup-event-facts/package_evidence.py)。ZIP原件 bytes/SHA、成员集合与CRC核验一次通过。原外置 INDEX/SUMMARY/报告均原样保存，历史 R42 RED不改。此次无新测试、SDK查询、游戏操作、存档正文读取或原生扫描；不授启动成功、C3或产品业务信用。`open_kaishek` 为 not-applicable：仅归档已有JSON、源码片段与原收据，没有新增 CK3 语义执行。
