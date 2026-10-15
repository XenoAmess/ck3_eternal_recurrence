# N41 连续推进与执行开销修复（2026-10-15）

当前实际工作包位于 `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation41-cold-prep`。Game PID255216、原OBS与含决策悬浮窗的D盘录像保持；P04/P05/P06仅轮换SDK。30年及平均0.5秒/游戏日目标仍未完成，不能以短批次或静态修复代替。

## 已部署的请求扫描优化

旧 `generated()` 对全部历史inbox逐文件查is_file和outbox.exists，未完成的held FULL使它再扫描一次；请求越多，累计成本越大。631个已完成文件的5次单遍实测为49.9–54.9ms，中位约53.5ms。新 `pending_request_paths` 先在一次os.scandir中按完整后缀和未消费序号筛选，只对新候选查询文件/回执，同一目录中位0.740ms。该数字是局部扫描计时，不是整局吞吐提升倍数。

公共helper在 `tools/g2_saved_campaign/pending_request_paths.py`；P06实际部署字节SHA为 `126e8698b7c0305c69a08ce7607c5cc2749ba21d4e489f20118b8b5481a05da5`。外置 `ROOT-P06-PENDING-SCAN-VERIFICATION.json` 的8例覆盖旧完成、held FULL、已消费错误、未发布partial、新future request、多个pending、generated拒绝和历史zero-stat断言。队列主轮询与generated共享该实现；新序号和多pending拒绝继续生效。

## 原生查询仍是瓶颈

P04 `ordinary-stage-timings.jsonl`、Python PID250464中，`driver.native_command_result_wait/query-declarable-wars` 共30次、163.887秒，中位5.45965秒。语义快照6262次，中位约0.4ms；普通规划内部中位约0.134秒。阶段存在嵌套，不能相加当作总墙钟。宣战两次无实际操作后30日冷却仍在使用。

最新普通planner对任意final-legal CB已有general battle prior，因此不能把820条候选中的朝贡或宗教战争按名称硬删。完整查询对living character与enabled CB逐个原生evaluate；后续按CB原生聚合采样定位真正耗时，不把只添加诊断说成已经加速。

## 暂停、闭包和真实日期

P04原AUTO625失败后，pause628 ACK先到，629仍旧native908；631才真实paused/native909。公共修复见[暂停专题](life-advance-popup-pause-retry-2026-10-15.md)。P05整叶移植造成旧war-cash transport不接受新版driver的payment_sampling参数；原错误17保留，P06改为复用P04完整闭包，仅局部回补driver暂停和construction修复。实际P06源码8项暂停回归及旧payment调用签名smoke通过。

P06 AUTO155返回真实paused、请求8日而实际10日，外置分类器原有`elapsed > horizon + 1`额外限制误拒绝。纯分类器补丁已去除此非战术限制，保留日期算术、角色/episode/原生帧绑定、真实暂停、单日战术严格要求及配对after metrics；实际多走2日记录为overshoot。原155与4个负例离线验证后，156安装、157重新消费原回执均0 MCP调用、不重放动作。可复用精确补丁与输入/输出SHA在 `tools/g2_saved_campaign/patches/n41-observed-clock-overshoot.*`。

## 离线事件知识

P04已完成批次77/140/261/316的4类事件与1类交互已通过通用原版分析器查当前exact1.20.0.4源码、核原始before/after SHA、保存条件/作用域/选项及副作用来源，并发布到当前state的通用event-source-registry/interaction-source-registry：courtier_guest_management.0102、conqueror.1200、marriage_effect.2001、stress_threshold.1011、negotiate_alliance_interaction。报告在 `root-p04-offline-source-review01`，未解析项为0；源码知识不证明实际数值副作用，也不冒充最佳策略。

独立 `offline_vanilla_event_worker.py` 已持续处理完成批次并异步发布新知识，输出 `automatic-event-source-analysis01`。旧batch里的pending字段作为历史保留，以后继分析报告闭环；同来源/选项结构的新实例由通用source-rebind校验决定是否已知，其他机器未复制/重建知识时不能外推为已部署。

## P07 只读规划竞争的自动恢复

P06原188为继承人查询的暂停地图前置条件竞争；原435为`query-campaign-root-context-v1`读取期间实际战争数从1变2，原生返回具备完整request/result绑定的`state_changed` preflight。两者均未提交业务动作。P07同一Game内恢复后，普通规划已读取两场防御战；当前累计7619游戏日，约20.86年，30年尚未完成。

公共`readonly_planning_retry_v1.py`只对上述两类有证据的只读前置失败重新获取快照并规划一次；嵌套规划共享一次预算。动作拒绝、其他查询、缺失诊断、超时和其他异常继续返回原错误。它不重跑`auto_turn`或执行计划。实际service wrapper与正负例验证为3项测试、7项subtest通过；P07外置完整绑定与恢复组合证据分别在`ROOT-P07-READONLY-RETRY-VERIFICATION.json`及`ROOT-P07-TYPED-RECOVERY-COMPOSITION.json`。

P06完整批次6推进64日/50.175秒（0.784秒/日），批次67推进91日/55.397秒（0.609秒/日）。纯推进的70个完整窗口中位0.320秒/日，最快9日/2.024秒；原生snapshot每250ms发布一次，因此`.251秒`等待不能证明后台FPS限制。当前设置为fullscreen、VSync开启、framecap=monitor、adaptive_framerate关闭。只读报告在`D:/qperf15_artifacts/background-fps-readonly-review.json`，没有修改游戏设置或桌面；完整批次平均0.5秒/日目标仍未达成。

`driver.life_advance_wait_public_change`计时现附加已有快照的before/after日期、native revision与public revision六个整数或null字段，不增加等待或查询，用于区分实际游戏钟推进与snapshot发布等待。定向验证41 passed、1 skipped，覆盖计时开关、读回不可用、原返回对象及原异常保持；源码回执`D:/qperf15_artifacts/public-change-clock-source-ready.json`。针对P07冻结输入另备最小SHA绑定补丁，待下一必要冷载部署；源码通过不等于已有实机计时数据。
