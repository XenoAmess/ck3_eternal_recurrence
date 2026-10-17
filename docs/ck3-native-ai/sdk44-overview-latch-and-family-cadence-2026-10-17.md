# SDK44：独立查询解除旧关闭闩锁与监护查询冷却

`machine_id: xenoamess-full-tower-eb9d2c1186`。本批以公共 `344bd8e5` 为基线窄合两项修复，不修改运行中的 Game、SDK、OBS、录制或冻结源码。目标仍是先完成稳定30年，再达到小于1秒／日，最后0.5秒／日；当前均未达成，G2仍6/8。

## 原失败与修复合同

SDK43窗口10在推进1250日后于 FULL1747／AUTO1778 停止。SEM1779 在 raw53293416、Native5983／public1882 的独立查询确认通知窗口当前可见；旧 pending 却仍指向 AUTO617、Native4732、raw53273664。AUTO617 的原生关闭回调已完整返回且 handled=true，但后读仍可见，状态为 `verification_pending`。这些证据不能证明当前窗口与617是同一实例，也不能把 handled 或窗口战争数变化当作关闭成功。

新的 transport 只对已完整返回、不可继续收取的该类关闭记录处理后续独立查询。当前查询必须通过既有正式合同，并保持 owner／actor／episode／connection 绑定，日期及原生版本不倒退，ticket 和 GUI pump 均严格更新、线程相同。满足这些条件后归档的是旧命令的执行不确定性，字段仍明确 `callback_completed_closure_unverified`、不重放原动作、`close_action_credit=false`。超时、缺失完整响应、外国帧或未完成命令仍保留 pending。

独立后查确认 absent／hidden 时无需再关窗；确认 visible 且已到新原生帧时规划器可建立新意图。同一原生帧仍可见则延后重试，避免零日 close／query 循环；后续帧仍须重新查询。原查询失败不变成 absent，旧关闭回调不变成业务成功。

## Family 查询冷却

只对和平、暂停、地图就绪、无事件／交互／终态的完整同帧监护教育输入缓存否定观察。首次查询与明确选项物化后的第二次查询，必须都由原生完整、同源地否定同一 ward／guardian 对；同一日期不重复计数。两个不同日期的合格否定后，最多30游戏日延后该对的昂贵查询。同帧可复用已完成观察，其他子女、婚姻、教育 focus 等规划继续运行。

诊断明确标为 `same_frame_negative_reuse` 或 `policy_deferred`，当前原生合法性仍是 `unknown_without_fresh_query`，不发明新查询、不授动作信用。court、guardian、focus、年龄、actor、heir、episode、连接变化会改变资格；出现真实可提交意图会清除旧否定记录。状态仅在 Service 内存保存，冷启动重新查询。本批不宣称实机提速或此30日策略已获得独立业务验收。

## 验证与实际边界

公共源码的41项定向及既有回归测试、15项 subtests 通过。新覆盖为8项通知 transport／正式 normalizer／普通 planner 测试，以及4项 Family helper／真实 Service 方法测试；Native I/O 使用替身和明确标注的已完成小投影，不声称完整实机或整个 auto 链已离线重跑。Service AST 比较确认只修改 `_plan_private_family_education_v1`，原 Holy Site、镜头及其他公共功能保留。新测试加入既有CI步骤，不新增完整矩阵。

[SDK44首批实际小投影](evidence/p44-first-actual-recovery-2026-10-17.json)记录 Root owner57800 首次启动成功：新 AUTO6 关闭回调返回后仍是 `verification_pending`，AUTO8继续普通查询；AUTO16／MET17 首次正向推进7日，FULL3的20轮累计推进20日。内层新查询完整审计未从AUTO体导出，因此不反推具体窗口实例已关闭，不给旧617补信用，也不据20日宣称持续稳定30年。运行包与公共源码各自冻结，不为本次公开提交重启现场。

Root随后交付的窗口11截点为 commonrunner19579、baseline53293896／target53556888，同一Game51028与5ebe录像接续。此处只记已启动接续，不是实时运行指针或该窗口最终结果。录制observer88539已装，只在已分类的恢复后等待MET资格下接续；尚未遇新录制故障，不授其实机恢复信用。

前一公共提交 `40be6806` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39036726683)及[线性历史检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39036726665)均已成功；此结论只绑定该提交。其后外部 `3d7a9f11`／`344bd8e5` 已保留并线性同步，不能借前一CI结论外推后续提交。

来源及公共文件 pins 见[本批来源清单](evidence/sdk44-public-transplant.json)。大 Driver、SAVE、原片和运行队列不入库；原失败和只获 ACK 的记录保留。
