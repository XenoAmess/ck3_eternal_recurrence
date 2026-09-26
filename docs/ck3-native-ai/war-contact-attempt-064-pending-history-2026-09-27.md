# R064 三军接触观察：第 41 天交互阻断与查询历史边界

本页记录 CK3 `1.19.0.6` 的一次**实机观察及工具链工作流结论**。它没有证明三支军队最终如何接触或战斗，更不能把 pending 查询的重复循环写成游戏原生 AI 规则。对应的原生军队接触树仍以 [army-contact-resolution.md](army-contact-resolution.md) 为准；交互类型化字段以 [pending-interaction-special-war-binding.md](pending-interaction-special-war-binding.md) 为准。

## 冻结输入与观察结果

- 064 从 058 的 `three-split-routed-immutable.ck3` 开始，源存档 SHA-256 为 `77BE86B0FDE44D348807B201B9809A29F8099A4FF005A9C12D632045B4AB0DE9`。独立会话使用空 mod 列表，Steam 离线截图与回执先于 CK3 启动；没有调用 `xar-promo`，没有录制正式视频。
- 三支目标玩家军队为 ArmyID `18`、`32`、`33`，玩家 CharacterID `29829`，活跃战争 WarID `4`。观察器每次只推进一个原生游戏日，并在同一暂停帧读取目标军队及 CombatID。第 20 天保存的不可变检查点 SHA-256 为 `306377F9E5A086AAB52938622B9114ABDF1D3FEAC06537475392B48D8973DA55`。
- 064 在相对第 41 天、`date_raw=53145504` 遇到 pending CharacterInteraction instance `33554522`，发送者 `32522`；此前未观察到三支军队共用同一 CombatID。结果是 `planner_selected_no_supported_pending_reply / INCONCLUSIVE`，没有替规划器选择回复。阻断存档 `pending-blocker-immutable.ck3` SHA-256 为 `55FFD6033DC9910A0A1A32BDD05DAA904D10641AB2BF7D6F6ACF779D80A31ECF`。
- 原始目录：`D:/workspace/ck3_native_war_ai_promo_work/episode01-losing-side-contact-attempt-064/`。`contact-summary.json` SHA-256 `1B1E4D1AB32F10829971CF76E4195A0A7F243DC1FC429342BC3D21D8BBD780EE`；`ck3-output/session-result.json` SHA-256 `82D30939929A85927B163E95A7E68689EB12F809D02A071690CCFF563F0B9AAB`。后者的 `shutdown.cleanup_proven=true`、`job_active_processes_final=0` 且最终 CK3 进程清单为空；任务总线 CK3 资源已释放。

启动前的逐文件 shadercache 复制和 SHA 校验持续超过观察器首次 `900` 秒等待窗口。首次观察器因 interactive 服务尚未出现而退出，**未执行任何游戏动作**；同一份观察脚本随后重新等待，正式服务就绪后才开始推进。该环境准备耗时不是游戏日数，也不改变上述存档配对。

## 为什么类型化查询成功后仍再次查询

第 41 天 `ck3_plan_turn` 的前置规划选择 `query-pending-character-interaction-context-v1`，phase 为 `pending_war_interaction_query`，回执 `042-pending-plan-before.json` SHA-256 `D73957B4B31AD1D6697F6ED5D05CA5CB047468577ABD4A369DBC6323394A9AC7`。

观察器随后直接调用 `ck3_query_pending_character_interaction_context_v1`。`042-pending-typed-context.json` SHA-256 为 `95AF92254D13BF6363398C24DD9C33D93C115881226AED0A3B967F4BC5D942A3`；它返回 `accepted=true`、`status=available`，准确绑定 `snapshot_id=native:128`、公开 `revision=129`、`native_revision=128`、`date_raw=53145504` 和 instance `33554522`。类型是 `arrange_marriage_interaction`，原生 reject 合法。`pending_character_interaction_context_ready=false` 指**完整语义尚未闭合**，不否定上述身份与合法性字段，也不是重复查询的直接原因。

问题出在 **064 当时版本的回执进入规划器的路径**。当时直接 typed MCP 调用走 `GameplayBridgeService.query_pending_character_interaction_context_v1` → `NativeHeadlessGameplayDriver.query_pending_character_interaction_context_v1` → `_execute_primitive_step`；这条路径返回查询结果，但不调用 `_record_command`。相反，当时的 `NativeHeadlessGameplayDriver.execute_step` 在执行成功后写入命令历史。`042-pending-after-query.json` SHA-256 `7E37ECC621E7DC899A3B41B510520B0566EBCE9A52155C0AC4162EEDE5B93E2C` 与查询前仍为同一暂停帧，但 `native_command_history` 的 42 行只有 41 次 `life-advance` 和一次 `save-checkpoint`，没有 pending 查询。策略的 `_same_frame_pending_interaction_context` 只从该历史寻找已成功且同帧绑定的查询。因此后置 `042-pending-plan-0.json`（SHA-256 `F1C30FE53423DC50BF80CE720D0B81F4C89165BDBFEE4A268C5A26092C143ABE`）仍选原查询。生产修复已在 master `7ec925a7ada949b7403d1f9f6ef95ebe1df76277`：direct typed 查询现在通过可记录的语义路径进入历史；服务测试 25/25（含一次真实 NativeHeadless history 回归），另三组相关测试 45/45 通过。**这不追溯改变 064 的旧回执，也不等于 MCP → 规划器的 CK3 实机链路已验**；仍需独立的 067 实机复验。

代码锚点：`ck3_autonomous_player/src/xar_autoplayer/strategy.py:1096-1163,7851-7939`；`ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py:5704-5724,15079-15229`；`ck3_autonomous_player/src/xar_autoplayer/bridge/service.py:578-649,9756-9853`。现有 `tests/unit/test_gameplay_bridge.py:531-599` 在 fixture 中**预先手工放入**查询历史，并测试了后续规划；它没有覆盖“直接 MCP typed 查询 → 命令历史 → 同帧重新规划”的真实链路。

## 后续执行边界

已准备的新 067 独立尝试从 064 阻断存档和 `042-blocker-save.json` 的精确 SHA 配对恢复。先要求生产规划器选中查询，再通过 `ck3_execute_step` 执行它，核对同帧 typed 结果和历史写回，然后重新规划。**仅当规划器明确选中 `reject-pending-character-interaction`、该步已发布且 typed legality 同帧允许 reject 时才提交拒绝**；任何其它回复、旧帧或不一致一律保存阻断证据并停止。最多推进 110 个原生游戏日，最多四次这样确认的拒绝，独立保存相对第 20 天和三军共战时的检查点。067 当前仅静态准备，尚无实机结论；066 占用 CK3 时禁止启动。

生产修复的验收标准是：direct typed MCP 查询与规划器消费的命令历史属于同一可信证据链，且**恰好记录一次**，避免 typed 方法和 `execute_step` 双重写入。新增测试须从真实 MCP 查询入口走到 `ck3_plan_turn`，同时覆盖旧帧、错 instance、查询失败、缺历史及合法拒绝门禁；不能仅用预填充 history 的单元夹具宣称闭环。064 的重复查询已由旧版本证据证实；修复后的可用性以其自身测试和新的实机回执为准。

2026-09-27 后续状态：上述“067 当前仅静态准备”是 064 写作时的状态，不追改 064 原始结论。067 已在独立实机会话复验查询历史写回、同帧重规划与三军共同接战；原始回执和适用边界见 [067 证据页](war-contact-attempt-067-same-frame-common-combat-2026-09-27.md)。
