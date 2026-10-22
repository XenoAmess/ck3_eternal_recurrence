# 活武器真实存档冷载验收

本适配器的源码与离线回归已经实现；**实际冷载仍为 `NOT_RUN`**。本记录机器为 `pc-20260924rtuf-f11af23c08`，观察日期为 2026-10-22 UTC。离线检查与旧场次来源复核的精确时间、命令、退出码和文件 Pin 见 [源码验收索引](evidence/cold-persistence-source-ready.json)。其他机器须重新核机器、运行环境与存档来源。

入口是现有公共 `startup.saved_campaign`，复用共享 v2 profile materializer、正式 staging 校验、单次 `-loadsave=restored_campaign` 和真实 `saved_campaign_restore`。新增适配器没有原生实现，没有写入预期终态的游戏 fixture。登记草案单独保存在 [cold_persistence.registry_stanza.json](../tools/cold_persistence.registry_stanza.json)，尚未合入公共产品清单；登记并冻结新的执行树后才能由 Root 调度新场次。不得热改现有冻结场次。

数据依次经过以下真实生产路径：

```mermaid
flowchart LR
  A[原场次 MCP Save 和只读装备结果] --> B[原 checkpoint producer 保留原件和严格 melt]
  B --> C[原 callback 与存档消费者重新验来源]
  C --> D[正式产品 v2 profile 与公共 CLI restore]
  D --> E[实际 player/date/CampaignRoot/推进的 owner pump]
  E --> F[新场次一次 MCP Save]
  F --> G[现有 root checkpoint producer 与全部 readback 消费者]
  G --> H[重新计算六项持久化比较]
```

准备参数必须同时提供公共 `saved_campaign` 的 `save`、`bytes`、`sha256`、`player_id`、`date_raw`，以及下列八个闭合 `case_inputs` 字段。Pin 的格式沿用公共合同：`{"path": "绝对路径", "bytes": 整数, "sha256": "小写SHA256"}`。正式产品目录使用路径，`plain_configuration` 使用现有配置文件 Pin 映射。

| 字段 | 实际来源 |
| --- | --- |
| `product_dir` | 正式 builder 本次生成的 staging 目录 |
| `formal_manifest` | 与该 staging 对应的正式 manifest Pin |
| `plain_configuration` | `pdx_settings.txt`、`tutorial.txt`、`presets.txt`、`player/game_rules/presets.txt` 的 Pin 映射 |
| `source_run_context` | 原实际场次的 allocated run-context Pin |
| `source_runtime_manifest` | 原 frozen argv 所绑定的 runtime manifest Pin |
| `source_checkpoint_observation` | 原 core、threshold 或本 cold observer 的已验证 checkpoint JSON Pin |
| `source_save_native_record` | 原 checkpoint 对应的成功 `ck3_save_checkpoint` actual-results Pin |
| `source_item_native_record` | 同一暂停日期、角色和进程的只读装备查询 actual-results Pin |

`saved_campaign.save` 必须指向原 producer 已保留并验证的不可变原存档，字节数、SHA、角色和日期均来自上述消费者，不能手填预期游戏状态。原 MCP 保存槽以后可以被正常使用；适配器仍以原 Save 回执、原 request 和保留原件的身份闭环核对，不要求旧槽位永远维持旧内容。来源机器、原 run、实际原生进程、装备归属和完整 producer 请求均须相符。

优先选择未来 `suppression_timer` 的真实 renewed checkpoint04：应在合法续期动作完成后，以实际 observer、Save、装备查询与 readback 确认期限、月链和序号，然后取其原件。`xalw.10` 的 renew 选项不会像喂养确认一样返回管理事件，这有利于公共冷载直接恢复。本文尚未读取该未来保存点，期限 `+180`、chain `2`、seq `1` 是 Root 指定的待核来源目标，不能当成已经观测的存档值。若实际种子缺少喂养印记，该项如实 `BLOCKED`，无须为四档印记另开四场。

R8 checkpoint07 已有一项真实来源复核：当前消费者只读重验了旧实际 Save、原官方 strict melt、callback、存档内容与原生装备结果。保留原件为 `observations/pc-20260924rtuf-f11af23c08--living-artifacts--R0008/checkpoint-07/original.ck3`，70,733,402 字节，SHA-256 `6d36a1f34cccf41d3cc31b5218869e957108fe166963690155e1ed23905d28a9`。原目标 402、主人 31254、1066.11.1，6 级 / 580 XP / 成长计数 5 / 共鸣 25，四件材料均已消耗；实际唯一印记为 `type=flag`、`flag=primary_armament`、无 raw identity。此结果证明旧真实来源可以被新消费者消费，没有重新运行 producer、发送游戏动作或冷载游戏。原业务证据及旧回执保持原样。

每个新场次只进行零日恢复和一次实际新 Save。适配器先消费真实 `saved_campaign_restore`，从完整原生帧读取玩家、日期和进程，核对正式 v2 profile、原件 SHA、实际启动 argv、CampaignRoot 与帧的 snapshot/revision/date 对应关系，以及至少两次推进的 owner pump。公共 `Session` 使用显式 typed binding；原 Robert 前台绑定继续由原调用方使用。只写 `ready`、伪造 ACK 或跳过真实 root/pump 不能绑定 cold 会话。

新 Save 经现有 `root_checkpoint`、实际 producer、strict melt 和原闭合 readback consumer 产生新观察。独立 `verify_case` 再次消费新旧来源及实际 host restore，重新计算结果，不能用保存下来的 `PASS` 文本替代。producer 的合法空 stdout/stderr 只在原已验证日志边界允许；其他空证据不获豁免。

| 比较项 | 通过范围 |
| --- | --- |
| `COLD-GROWTH-STATE` | 同角色、同目标、同暂停日期的新 Save 中，完整已解析 sample 相同，包括等级、XP、pending、成长计数、最后成长月份等现有字段 |
| `COLD-ALL-ARTIFACT-VARIABLES` | 名字与全部已解析 `xalw_` 变量的 presence/type/raw identity/flag 相同 |
| `COLD-SUPPRESSION-DEADLINE` | 源中存在正的整值期限，新旧保存表示相同 |
| `COLD-SUPPRESSION-TIMER-SEQUENCE` | 源中存在非负整值序号，新旧保存表示相同 |
| `COLD-FEEDING-IMPRINT` | 源中存在合法个人装备类型 flag 的唯一 `xalw_feeding_imprint`，新旧保存表示相同 |
| `COLD-SURVIVING-MATERIALS` | 剩余稀有度精确 tuple 和实际材料 ID 集合相同 |

缺字段或源字段类型无效时，相应功能项为 `BLOCKED`；有效源在冷载后变化则为 `FAIL`。即使两侧同样错误也不能授予该功能项通过。六项均通过才满足此 cold case；其他项的独立结果仍保留。结果始终不授予整体产品或发布资格。

这里比较消费者实际解析的保存表示，不证明 expiry 元数据、延时事件触发、成长推进、续期防旧回调或四种稀有度的独立印记效果。游戏只保存一个 `xalw_feeding_imprint`；四次喂养后的最终存档不能证明四个独立印记。R8 的喂养业务证据仍见 [R8 记录](runtime-r8-continuous-growth-and-feeding.md)，计时器和阈值需要各自实际运行结果。

来源不新增“保存时必须无事件”的门槛。管理页内的合法用户 Save 仍是合法来源。共享 host 当前 `saved_campaign_admission_frame` 在未提供既有 startup-case 合同时拒绝非空 `active_event`；`wait_for_saved_campaign` 仅在已有合同和实际 admit proof 下放行。此次适配器没有放宽或绕开该合同。若恢复后受此现存能力限制而不能绑定，应保存真实诊断，选择另一个已实际生成的来源点，或交由 Root 使用已有被支持的启动合同；不得编辑旧 Save、伪装无事件或把未知弹窗忽略成通过。

正式执行仍由公共 `prepare → allocate → preflight → run → verify` 顺序调度，消费每步真实退出码。`prepare` 使用上述 inputs 与标准 seed；公开登记合入前不要直接运行草案。示例参数组织须以 Root 当次 frozen runtime、products、prepared-case 和新 run-context 为准，不能沿用 R8/R12 的运行时身份。共享正常退出及资源释放由原 CaseClient 完成；此 adapter 的结果不会代替实际 retained OS0、native0、cleanup 或 Steam 后台离线回读。

离线回归包括实际正式 builder/v2 materializer/host copy、提取真实 host restore 函数的 native 边界测试、实际 Session 与 root producer/readback/verify 闭环、来源错身份/错类型/字节漂移、不同来源功能缺失、结果重标记和序列化差异。测试中作者构造的存档与 native 边界明确属于 authored 测试，不能据其宣称实机恢复。官方 melter 对 authored 文本头返回 `Invalid header` 的一次真实失败也保留在外置回执中；该失败没有被改写为通过。正向真实来源闭环使用上述原 R8 已成功的官方 producer 原件。

持久 CI 为 [living-artifacts-cold-persistence.yml](../../.github/workflows/living-artifacts-cold-persistence.yml)，执行产品工具测试、六个完整文件 strict mypy、共享 v2 profile 测试和独立 SDK saved-campaign profile 测试。本机 209 项完整产品测试先通过；发现并修正测试导入的 strict 错误后，复跑 13 项受影响测试，再顺序执行余下三条 CI 命令，均退出 0。保留原失败 attempt，不将其原样标绿。

另已实际执行现有全模组 strict 入口，52 个完整源文件通过；仅为该次命令补齐 SDK `src` 的 `MYPYPATH`，未设置 `PYTHONPATH`，并禁用缓存。旧 `static-ci.yml` 的对应环境仍待 Root 合并时补这一条路径。两种静态检查均使用 `follow-imports=silent`，不能外推全部共享历史模块全绿。精确命令与日志 Pin 见开头索引。
