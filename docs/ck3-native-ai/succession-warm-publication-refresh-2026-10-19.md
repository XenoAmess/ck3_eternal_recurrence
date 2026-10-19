# same-PID暖恢复：公开revision域变化后的继承预测刷新

`machine_id: xenoamess-full-tower-eb9d2c1186`，实际读回 `tools/ck3_live_run_id.py machine`（chunk `1a471d`）。离线诊断始于 `2026-10-19T06:03:07Z`，最终定向测试完成 `06:10:43Z`；[机读证据](evidence/succession-warm-publication-refresh-2026-10-19.json)固定来源。没有操作Game、MCP、桌面、SAVE、活Driver或运行COW；所有runtime文件写入由唯一runtime owner完成，本任务仅读冻结小回执与固定源码。

## 实际失败与精确原因

C5 `AUTO255` 实际在 `06:00:38.447748Z`—`06:00:38.503954Z` 返回563B完整错误：`retained estate differs from the current actor/episode sequence`。原件SHA `2169d7152cc02bf3b59c39d72f8161fe5c5c5ac151b67bc66f6c537853b93d52`；没有重发255，没有授予完整周期99或新游戏日信用。

runtime owner只从已经关闭的C4 Driver投影旧期待，未读取活Driver：前代/当前仍为31254、episode仍为 `native-31254-6271ac8cd441`、日期仍为53146896；旧期待为 `snapshot_id=native:60/public revision61/Native60`，实际暖恢复SEM252为 `native:61/public2/Native61`。CAP253已证明 `same_pid_hot/active_resumed`。Native/date未回退，公开计数重起。

精确冻结src04/业务 `6ebbffcdebe3e30353513e0984572ebc701daa2e` 的 `NativeProtocolState.__init__:1077` 每个SDK对象令 `_public_revision=0`，其后随该对象的publication变化递增；原 `same_pid_hot` 分支11639恢复旧完整expectation。新Service `_prepare` 发现帧不等后取得新root；完成独立同帧校验的fresh-root hook在原新retain前调用纯比较。旧纯叶把61>2当作同一序列退序而拒绝。此处失败不表示actor、episode、Native时间或真实estate发生退序，也不能据此重签旧title事实。

## 本次现成恢复入口的来源证明

精确src04控制流证明：Native `execute_step:9430` 在返回Service前已 `_record_command(ok=True,result)`；原11096附近把完整root追加到同resident内存history。该唯一pure错误只能在Service已构造且独立校验完整新root response后触发。因此255发生过规划只读查询，不能称0Native。

`auto_turn:4771` 的 `plan_turn()` 未完成即抛错，4779的 `_execute_planned_turn` 未到；其后before-submit与本次selectedbusiness dispatch未发生。runtime另外封存0255-0-plan.json及publish.lock不存在、后续callback ordinal为空的2054B实际回执。文件absence自身不能独立证明无业务，需与这个源码抛点结合。

原 `_prepare` 1555—1581从history挑同帧ok root，传 `_planning_root_result`；该缓存仍经原绑定校验，但不再调用fresh hook，继而沿原1626 `retain_succession_expectation_v1` 从真实bundle冻结当前预测。这是同resident且帧仍匹配时的现成恢复路径。Queue原halt仍阻止直接PLAN；Root/harness负责极窄本地清255已证未dispatch的pending/halt后，使用新编号只读PLAN，不能重发255，也不能跳过Queue守卫。本文不代替其实际PLAN结果；若帧改变或严格retain拒绝，保真实halt，不自动重试AUTO。

## 永久源码修复

原 [纯比较守卫](../../ck3_autonomous_player/src/xar_autoplayer/bridge/succession_expectation_invalidation_v1.py)字节未改，SHA仍 `33a1905f3e142e7784165dc706d2be0749e9a74d4745c9c43fe975689c1ca3da`。未删除公开revision检查，也未放宽actor/episode/Native/date校验。

新增 [小纯叶](../../ck3_autonomous_player/src/xar_autoplayer/bridge/succession_warm_publication_refresh_v1.py)，只在Driver原restore kind明确为 `same_pid_hot`、公开revision严格降低、当前living/paused/map-ready、前代与当前actor/episode完全相同、Native/date非退时，验证**已完成的新完整root**：原 `build_turn_bundle_v1`、完整freeze和原binding校验仍执行；partial estate、混合来源或缺失来源拒绝。未命中这个特殊域变化就返回None，原纯比较继续负责。

满足所有条件后只返回detached的两派生字段清空及 `source_epoch_refresh_required`，保前后source binding、原query sequence，明确 `estate_change_inferred=False`。不采纳、不移动或重签旧estate。Driver在原fresh-root hook的同一把锁与同一current-publication/pair比较内消费，仍由原末尾CAS后应用、置dirty、锁外原persist。下一原prepare严格retain这一次真实root；不增加每AUTO查询，不改commandhistory、生命周期、goal或旧源证据。当前public已进入新域后，不会因restore-kind仍为hot而再次清除。

未知terminal或继承已改变actor时，Driver沿原分支保留前代期待给自然对账；新叶也不允许这种输入。未完整estate读回同样不能清除。本次没有修改Service、原同域纯比较、现有Native构建或已加载src04/C4/C5包；runtime当前仍以6ebb为业务范围，不能把本源码验证当作现场永久修复已采用。

## 定向验证与边界

只运行新增 [两项compound](../../ck3_autonomous_player/tests/unit/test_succession_warm_publication_refresh_v1.py)：**2 passed，1.49秒，exit0**（chunk `2953f6`）。实际生产Driver/Service方法使用合成Native材料；61→2/public、60→61/Native复现真实域形状，角色与estate内容仍是测试夹具，不是当前游戏新事实。

正例新root触发原锁内清除并persist一次；下一原plan复用刚完成的history root，额外root调用为0，再由真实retain持久化当前完整期待。commandhistory未丢，游戏动作0；同public再读不重复清除。原纯比较直接面对旧61/新2仍拒绝。负例覆盖非same_pid_hot、没有公开回退、actor/episode不符、Native/date倒退、terminal、partial、mixed binding，以及实际Driver在terminal时保原两字段零写。

首次运行1pass/1fail（chunk `55d565`）指出新helper自身应明确拒 `held_title_partition_ready=False`，即使Driver已有前置守卫；补齐该纯叶检查后上述最终两项通过。没有重跑已完成M3矩阵或赋予自然继承、保地、G2增项信用。Driver差异仅9增2删（含3行import）；未stage/commit/push，由Root统一合批。新小文件各小于20KB，无重型写入或删除，按通用存储策略1.0.0于 `2027-04-17T06:10:43Z` 复核记录。
