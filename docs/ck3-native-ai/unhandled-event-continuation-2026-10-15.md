# 未覆盖事件与弹窗：采集、MCP 续行、轮后离线补齐

2026-10-15 用户明确要求所有未覆盖事件先留证、当场选界面第一项继续，一轮后再离线分析、批量补齐；当前疾病事件由执行者自主决定。选择必须通过 MCP，不使用 OCR 或鼠标。该顺序覆盖旧的逐事件补 registry 后才恢复游戏要求。

## 普通运行路径

`choose_one_life_turn` 先保留已有可执行专用策略；未覆盖/合同无法消费的事件使用当前帧 `query-current-event-window-context-v1` 的真实显示选项。显示首项由最小 `rendered_index` 确定，再映射其 `native_option_index + 1` 为 `select-event-option-N`，不能假定 native0 就是显示首项。

`GameplayBridgeService._execute_planned_turn` 在调用既有 MCP/native 选择路径前，向本次 managed state 的 `evidence/unhandled-events/<incident-id>.before.json` 写入事件 definition ID、实例、玩家/episode、日期、公共/原生版本、root/saved scopes、选项和原处理缺口。提交后写同名 `.after.json`，分别保留 ACK 和 NativeDriver 的 `event_selection` 实际后验；ACK 本身不等于选项已生效。异常保存原结果未知状态，不重放动作。普通 plan/auto 都消费同一策略，不增加单机或特定事件白名单。

公共 core 返回边界统一承接 `active_event*` 且未产出动作的早退，覆盖缺 registry、extended consumer、专用策略缺变体及 material observation 阻点。已产出有效动作的专用策略继续使用。若首项确实禁用、没有真实显示选项或来源已过帧，只记录实际诊断；不能伪造点击成功，也不能把另一项冒充第一项。

本场独立 feeder 在每个成功完整批次后，把该批新增 before/after 原件路径、SHA、事件 ID、实例及选择整理为 `continuation37/p04-offline-batches/<control>.json`。汇总完成即继续下一批；离线分析线程按这份清单查原版定义、补共享 registry/policy。分析不占用游戏现场，不把“已调用找医生”记成“已雇医生”或“疾病痊愈”。

## 当前真实闭环

外置根 `D:/codex-ck3-demos/2026-10-14-robert-30year`，本场 `continuation37`，CK3 PID127268、同一 episode `native-31254-96253c58fd68`，仅 SDK 热替换，Game/OBS 保留。录制仍在 D 盘包含 Desktop1 决策窗，无游戏会话/单段录像时长或字节上限。

- 原阻点 `p02-responses/0604-1-result.json`：`health.1015`、实例6，registry `registered_contract_requires_extended_consumer`，未提交动作。
- 真实窗口 `p04-responses/0621-1-result.json`：calculated event ID4331015、runtime ordinal6679；显示 native `[0,6]`，首项“叫医生来！马上！”。root 是玩家31254，saved scopes 为 epidemic/disease_type/sick_character/new_memory，无 physician。
- MCP 选择 `p04-responses/0623-1-result.json`，SHA `7316fffbb0931bb3a550af4dd22fefcb34b78c822cd81e0d8a67d3aea91b5363`：`select-event-option-1`；原生 `old_event_instance_id=6 → new_event_instance_id=null`，`postcondition_verified=true`，native223→224。没有桌面输入。
- incident `a6f66b2f3951420888c2569b6b77c574` 的 before SHA `d9c693c67f21d447d2b30b2df58e41d24448c9e99c3f4cd6a331214878e4a7b7`，after SHA `ba8364f99cc93bd5d2c8a390db8f5915a77ef19f48ba9266ed87fe0f50597277`。
- 首个完整30-turn批次 control613 于 `2026-10-14T17:57:39.649121Z` 完成，累计1358周期，清单含该1个未知事件；下一批继续运行，同时启动离线分析。后续 immutable semantic701 已推进 raw53166936，active_event=null。

01 候选12项定向离线检查通过，02公共边界新增6项通过；其中原始0604/0605提供真实显示选项和 frame，缺失窗口 envelope 在早期测试中明确为 synthetic，不当作实机作用域证据。随后0621及实际 before 原件已取得真实完整作用域。仓库 portable tests 使用明确 synthetic fixture 验证普通策略和实际 Service 分发顺序，最终数量见同次提交的日报。

该批全部1个未知事件已离线分析，`event-batch-registry01/BATCH-ANALYSIS.json` SHA `3cb1a574a782146e4341115714ddd173f56124bf7ec53eef676ff375a6ad8cba`。共享 registry 增加无医生四 scope/native[0,6] 变体，继续保留原有医生≠患者合同、原版文件 SHA 和 max_occurrences=1；普通策略传入既有事实 history。可复用计数器仅统计同玩家/事件、有原窗口查询帧绑定及实际 event_instance_advanced 后验的选择，重复 Service/Native 行去重。无法资格时继续通用兜底。9项候选检查通过，合入后受影响 registry/fallback 模块61项/78subtests通过。该增量在当前P05尚未加载，不声称已经雇到医生或痊愈。

一次 SDK 启动曾在 RPC 前因外置 queue 默认 artifact allocation 小于 reply reserve 被拒绝；原607无 MCP/native 提交。修正启动参数后热恢复原 Game，未重放动作。该内部证据预留不属于游戏或录像时长/容量 cap。所有小型候选和原件继续服从统一存储策略的有限保护与复核，录像未设单段上限。

## 伴随性能增量

当前围城仍因先前 R0047 多日推进越界保留一日观察节奏。对完全相同原生 driver，Service map-center 直接调用已包含 paused/map、exact build、actor、前后帧及镜头落点验证的 typed command，减少两次重复 rich Service snapshot；其它 driver 保留原路径。离线返回值等价，snapshot读取3→1，仓库18测试/56subtests通过。实际新墙钟收益须在部署后测量，不把已观测的全部5.2秒镜头耗时预先记为已消除。

P05 实际观测6次原生镜头中位5.49秒，未证实上述快照优化降低总墙钟。随后实测 `tasklist /FO CSV /NH` 2.4666秒、完整 `ck3_process_inventory()` 2.6024秒、已绑定PID的 Toolhelp验证0.0464秒；另一虚拟桌面路径重复两次全机inventory，吻合原镜头5.178秒。新候选沿新鲜Native diagnostics绑定PID，保留进程身份/窗口归属/标题/Iconic/DWM/VD验证，另一桌面不移动鼠标；非Native回退在同次调用中仅清点一次。7项离线检查通过，随后与镜头旁路一并在P06加载。

2026-10-15 03:24 CST 补记：P06普通AUTO已经旁路原生镜头命令。独立单 worker 只使用已观察数据挑选热点意图，合并待处理意图，关闭不等待；共享Native pipe不再被镜头settle占用。返回 `native_command_submitted=false`，实际状态为 `selected_deferred_native_camera`，不声称镜头已移动；显式MCP镜头工具仍可使用绑定PID快路。业务帧来自已有规划snapshot，结果分类也不再依赖镜头结果。P06观测23次军力AUTO中位约4.46秒、18次日期推进约1.53秒；两者是不同步骤，不能把后者称为完整每游戏日耗时。

## 角色交互弹窗的真实闭环

用户进一步要求陌生弹窗选择左侧，并强调必须离线分析、下次不能仍未知。原版 `gui/interaction_notification_window.gui:58` 同一hbox先声明 `reject_button/Reject/CanReject`，后声明 `accept_button/Accept/CanAccept`；三个stock特殊通知模板顺序相同。实现绑定原版文件SHA和原生同帧legality，经既有 `reject-pending-character-interaction` 执行，不按字典顺序猜按钮，不使用桌面坐标。

原P06 AUTO1088因旧nonwar/nonreligious分类表阻塞。实际消息 `301989889`、定义 `request_clerical_chastity_interaction`、sender32887、recipient31254，拒绝原生合法。只清除已证明未提交动作的阻塞周期，SDK热换P07，同一Game PID127268、同一episode和raw53168256保留。新规则明确登记为宗教贞洁请求，不把它伪标非宗教。专用策略已有动作时继续优先。

P07 `1104-1-result.json` SHA `22f3031100ab0cd80297fe8591954bcb0cc58f5960367d49a462234406e7f774`：MCP AUTO选择左侧拒绝，`interaction_result.status=rejected`、原消息ID相同、`remaining_pending_character_interaction=null`、paused=true、native435。incident `fa3ba0412d1946fd973b1e6d0ceab2d9` 的before SHA `aa9667bbc3278974c3473fe1d2c71b1a6cbc9a6169c634c2b77eaca298a56d14`，after独立记录 `original_pending_advanced_verified=true`；资源与好感材料效果仍未授予信用。

离线分析已核原版 `common/character_interactions/clerical_chastity_interaction.txt`，SHA `9a7470b42d2f9bfed8a71932014a4c2f8d6fdcc24277f99f79238c5703010b8a`：接受进入五年贞洁誓愿流程，拒绝有虔诚/压力/好感代价。分析与实际闭环小回执位于外置 `pending-interaction-left-fallback01/CURRENT-REQUEST-ANALYSIS.json` 和 `CURRENT-REQUEST-ACTUAL-CLOSED.json`；当前与后续同key/hash分类均为 `registry_known=true`。新陌生定义仍先选合法左侧并保存于 `state/evidence/unhandled-interactions`，feeder每批汇总新增原件与SHA，交给离线分析，不能仅保留待办清单。

P06批0613的health.1015无医生变体已在P06/P07加载，上文“P05尚未加载”仅描述当时边界。P07合入后的事件/弹窗/镜头相关定向检查101项、134 subtests通过。

录制在19:04 UTC因旧overlay263396正常退出再次中断，退出起因未证实。旧段aaf保留，OBS实际正常exit0；当前换为有写入重试与明确退出原因回执的resilient overlay239988，独立owner持续存活。新段498552f1-0587-4fc1-ad07-6dd2d13a328e于19:20 UTC开始，Root亲审含游戏与决策窗的scene，P06本地attach1091、零RPC，再清理未执行阻点1092。此处恢复是人工执行，自动watchdog部署结果另记，不能据离线测试声称已自动恢复。
