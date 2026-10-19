# saved61 普通冷启动的薄 Queue

machine_id: `xenoamess-full-tower-eb9d2c1186`。实际存档来源为2026-10-19的197 SAVE与saved61-cold-seed51；后继新 Game、Native26、录制、publisher和冷启动实际结果尚须 runtime 独立读回。软件未来 SEM/CAP 样例不是现场通过。

[薄 factory](../../tools/g2_saved_campaign/saved61_cold_queue_v1.py)继承原 CleanRobertMainMenuQueue 的完整 `generated/full_loop/consume/persist/recording/storage` 流程，仅覆盖有限 cold preflight 与首 SEM/CAP。它不导入或复用已耗 MET110 once 工厂、不复制原结算算法、不发 Start、不重发旧 AUTO/MET，也不增加额外 cold MET：`before_metrics_response` 绑定真实 cold SEM，并明确 `before_source_kind=actual_cold_semantic_snapshot`，不把 SEM 伪称 MET。

真实197 checkpoint 为70300340B，SHA256 `cb385a8fd4be62b6e553a4d0a5575d50886e8d894dc8ed83173d9ae851d4075d`，history122、raw53145792、Robert31254、原 episode。seed51保74普通周期与T0 raw53144328；实际维护 SAVE 将 checkpoint_saved4→5、calendar61、dirtyfalse，其余普通计数不变。实际195清局部错误和197 SAVE小回执见[后验](evidence/c3-partial194-save61-actual-readback01.json)。大SEM196不由本审计重读；runtime 的 `SEM196-BINDING-CORRECTION52.json`1913B、SHA256 `18fc80c3a30708c4de970e4f30d8b29d447eb2f580a7f41038c3c0ae23708ffd`补正了原小 projection 未取嵌套 actor/PID 的空字段，原receipt仍保留。

冷启动只接受实际 `driver_state_restored:true/restore_kind:cold_checkpoint/episode_binding_state:active_resumed`、无 driver error/cold rejection 的 CAP。首 SEM 必须证明新实际 Game/pipe/birth来源、原 actor/episode/date61/goal/lifecycle、paused map、无未处理选择。Native revision允许新epoch从1开始，不与旧98比较单调。`self.initial_frame` 与 cumulative `before` 同为真实新cold opening61；T0 `start_date_raw`、月样本、评分和历史地图文件保持原件。C4原 camera gate 指向新的 `ROOT-CAMPAIGN-MAP-ADMITTED-C4.json`，继续核当前Game/录制/该opening，不放宽旧PID守卫。

admission的[字段蓝图](evidence/saved61-cold-admission-blueprint01.json)中占位引用必须由 runtime 替换为真实来源，不能执行占位文件。`cold_prelaunch` 使用既有正常 prelaunch 的小回执，记录 canonical `xar_autoplayer.native_session.validate_cold_start_checkpoint_for_pipe` 实际返回、它使用的 prelaunch Driver pin、精确 FINAL-C3-DRIVER-CLOSE52 ref及两个冻结Sway来源。factory核对后者的最终Driver880726B/SHA `0c7e6dbfd329249c6b1106ecd4e028b78e25292d72ce1cddad8db04d69f718dd`、history122、197 checkpoint；首cold SEM后不再哈希已被新Driver写回的 live文件。旧Game的forced cleanup exit1如实保留，factory不要求它normal0；旧SDK退出仍以原pair generation与实际kernel关闭receipt匹配。

C4 queue/entry/Native binder、SDK freeze、publisher started、mod absence、新Game generation与current map都取新current视图。factory使用M0已审 `root_decision_text_api_c4` 与 `root_continuous_segment_auto_c4`，避免旧C3 API绑定旧manifest。分类器加载函数的实际source filename/SHA必须等admission中的新pin；Queue现成 loader 的旧PIN文件名应由唯一owner作C4 literal变换。旧退出旗/旧录制job不能误指当前，原guard保持；归档与实际命名由runtime负责。

[组合资格工具](../../tools/g2_saved_campaign/qualify_saved61_cold_queue_v1.py)用实际197/seed51和明确软件构造的未来Game SEM/CAP/map，组合原 `full_loop/generated/consume/persist` 与原camera合同，验证cold Native1重绑旧98、74计数/T0不变；原FULL首新请求恰为AUTO75，在RPC前截停。错误日期、episode、same_pid_hot CAP均拒绝。[软件资格](evidence/saved61-cold-phase-software-qualification01.json)没有声称preflight、未来Game、Native26或录制实机通过。runtime以真实新输入做正常preflight/SEM/CAP/current-map后，才允许首普通FULL；实际后验另存。

最终factory15895B，SHA256 `82d40a057f5091094728c0ca1a77cdb990c8b649b6c2ce2199f8dde53d2b44d9`。这是正常cold连接叶，不是额外平台或批准流程。来源review在维护实机验收后7日复核用途；按统一存储策略清理过期派生副本，保留仍为活跃输入的必要原件与理由。
