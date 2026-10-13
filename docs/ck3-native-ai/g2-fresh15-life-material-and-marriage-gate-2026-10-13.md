# G2 fresh15：LIFE 材料完成与婚配版本门槛（2026-10-13）

fresh15 实际完成两个普通 Service 周期：焦点提交 pending，随后原 ID 的独立 applied 材料回执；Service 随材料保存检查点。循环日期推进仍为 0。第三 AUTO 在婚配只读投影查询阶段返回 RED，没有婚配 before-submit 计划或动作。完整30回合演示、稳定战争和跨代仍未完成。

## 本场实绩

本机外置根 `R = D:/codex-ck3-background-spill/g2-remediation-20261013`，attempt `R/fresh-robert15`，实机编号 `xenoamess-full-tower-eb9d2c1186--eternal-recurrence--R0009`。冻结 clean master `2fbc4de52ea7430547e4335da8911246d67da540`，复用 B12；Game126152 / creation `20261013130150.616193+000`。新 state/profile/pipe，不恢复旧 SAVE，完整普通规划器。

Root 亲审 armed review002 主菜单后唯一启动录像，实际增长3,149,824B，配对 SDK 后执行固定序列。route1 0.084秒；New2 verified 0.082秒；Robert Start3 verified 27.489秒；camera4 centered 4.996秒；semantic5 0.004秒。Root 亲审 sample015 暂停特拉尼／阿普利亚地图后 SAVE6 saved。地图日期与原始帧均为1066-09-15/raw53144328。相机回执与进入循环之间约14分钟的准入等待不算游玩，也不作为第三查询错误的原因。

full_loop7 仅启动一次。`sdk-session01/LOOP-0007-TURN-001.json` 记录 AUTO9 焦点 `martial_authority_focus` 提交，原 ID `life-focus-6d00f314ef034bd3a8f013aa57031040`，episode `native-31254-b7eb635be2be`，仅授 pending 提交。

`LOOP-0007-TURN-002.json` 记录 AUTO11 原 ID `applied`、`postcondition_verified=true`，独立后帧 `native:4`，当前焦点匹配，Service gate进入 `await_consumption` 且 `checkpoint_saved=true`。这是实际材料证明，不是 fixture 或 ACK 推断。两周期 paired metrics 的 date_delta_raw 均0；定期每5回合 checkpoint 尚未到达，不能把 Service 内部 SAVE 计作第5回合保存。

AUTO13于13:22:39Z提交，5.344秒返回 MCP is_error：`marriage projection private query RED: five distinct current final-legal candidates and same paused revision required`。没有 `0013-0-plan.json`，没有婚配动作提交信用；保留原请求，不自动重试。失败原5候选、投影 request ID 和完整帧未持久化，不能从笼统错误反推其它资格通过。

## 已确定的版本前置缺陷

原生 `ck3_autonomous_player/native_bridge/src/bridge.cpp` 的婚配投影 request_valid 只接受 Reviewed ABI 为1.19.0.6或1.20.0.2。1.20.0.3的reviewed ABI映射到.2；当前真实1.20.0.4 SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518` 不在这两个值中，故必定提前拒绝。该分支下方已有 exact `.4` descriptor/family/projection绑定，但前置拒绝使其不可达。

Python transport发请求前已经要求恰好5个 distinct、每个都唯一 final-legal，并校验同一暂停帧；少于5不会产生本次 Native RED。修复应只补 exact `.4` descriptor 前置，继续保留5 ID、legality sequence、revision、heir、connection、暂停快照及 final-legal 条件。下方 `.4` 绑定存在不授该功能实机通过；新构建和独立场验证仍待执行。

后继还需有界失败回执保留同一请求的ID/5候选/帧/Native error，不导出全部history、不重发动作。外置治理 queue 候选已补 Council/Construction 的精确 typed 分类，8项新focused fixture通过，原LIFE/trace函数保持不变；本场 SDK 已加载，因此没有采用该候选或热改内存。候选与其5,113B交付回执见 `R/resume08/m_harness/queue-governance01/`，源码 SHA-256 `1335c1cab391577548be9d212f65615e60577871643b8523184fd8ad98c9f455`。Fixture不授治理业务信用。

## B12 实际读取的纠正

fresh14原始plan12已实际返回完整owner-tree的宣战通知 `available=true/accepted=true/status=hidden`，同一 owner ticket116 的 published/executor/completed一致。原件 `R/fresh-robert14/ROOT-B12-ACTUAL-OWNER-TREE-HIDDEN.json`，源response SHA-256 `50e6b8752a5bfc914ad38e382737cc4a78152365fba47565bef7958ed31ec1c2`。fresh15 Driver history index16再次取得同类hidden结果（ticket123）。**B12节点预算阻塞已在暂停地图的隐藏窗口场景解除**；不授可见通知关闭、真实战争或整局稳定信用。

旧fresh14发布文档中的“B12完整owner-tree未验收”是当时尚未提取原plan材料的状态，保留历史正文，以本段带日期纠正为准。后继 Native diff 守卫必须检查实际路径 `ck3_autonomous_player/native_bridge`；旧 helper错查根 `native_bridge`，不能把其通过作为无变更证明。Root另按正确路径实际核70fd8182至2fbc4de5，diff为空，故本场复用B12没有遗漏Native改动。

## 闭场及存储

Root13:24:20Z请求闭场；13:24:57Z supervisor closed，Game owned force1/tree_gone，queue224920 / FILETIME134363704192272462 exit1，application266200 / FILETIME134363704210016440 exit0，均原句柄观察。keeper停止，屏幕CAS4033→4034释放。独立录像COMPLETED 630,231,463B/1049.000秒，SHA-256 `df50dd99f1b8e8104fe6943ac27a26d1b7a28f588cc36dbc1e5328fc4b6e3daf`，输入解除、OBS正常exit0。实际摘要 `R/fresh-robert15/ROOT-ACTUAL-CLOSED-EVIDENCE.json`。

owner `/root` 保护本场LIFE材料原响应、回合回执、Driver、canonical/seed、关键图和录像用于下一场对照，原复核仍 `2026-10-13T16:58:39.018273Z`，不自动续期。Steam保持用户保证的离线状态，没有新鲜离线像素信用。

本场启动前实际删除两份fresh14精确相同方便SAVE及fresh09/10/11三原片，共5件／1,290,973,255逻辑B。旧三原片不可重建、已不可读取；所有旧PNG、原响应、超时/正常退出证据、SDK/source、fresh12 crash和fresh13 UNKNOWN录像保留。fresh11原片也含迟到暂停Robert地图，其原图sample010继续保留，fresh15不解决旧未知请求。精确可用性及用途边界见 `R/resume08/m_storage/GC-ACTUAL-FRESH15-CLOSE-20261013.json`，SHA-256 `d274145ce424d9157fc2294f0f22170628c1ebd03fd60501f0b621237682bd2b`；物理allocation未知。

fresh15原子准入去重6,572,188,684B，新1.88GB峰值后余137,745,908B。B13增量构建及下一场必须重新准入，不增加原8GiB共享预算或2GiB Native子预算。
