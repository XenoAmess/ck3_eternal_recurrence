# R206：实证 exact-day policy、原拍摄 RED 与正常闭场

来源机器 `machine_id: desktop-3fevhd2-1c74096080`；场次 `desktop-3fevhd2-1c74096080--vanilla--R0206`，实际冻结 source `7a342116d8aaa8a4c645941199c3ef1abd0a7c8f` / a36，索引观察时间为 2026-10-18 04:33:16 UTC。[原件与身份索引](evidence/episode04-r206-william-exactday-12004/INDEX.actual-a01.json)保留完整 path、bytes、SHA 和实际范围；[原采集者说明](evidence/episode04-r206-william-exactday-12004/README.md)保持原字节。这里只保存小索引，不复制原片、完整查询或存档。

初始 William 正常 checkpoint 的 raw date 为 `53147376`。唯一一次客户区 Start/Finish 得到 8.3 秒、1280×720 原片。片中 composite 实际完成一日到 `53147400`，独立 after 为 paused/map-ready，native clock 停在目标日期，overshoot=0。原 actor 仍为 **RED**：共享后验合同当时只接受 R203 的 `exact_one_day_unavoidable_contact`，误拒了 R206 真实 `exact_one_day_noncombat_native_speed_5`；不能把后来修码追认为原 actor 成功，不重发已成功的日步，也没有第二次 Start。

共享 [exact_one_day_postcondition](../../ck3_autonomous_player/src/xar_autoplayer/bridge/exact_one_day_postcondition.py)现只接受上述两条有实证的 policy，并继续逐字段核 composite、前后独立日期、episode、paused/map-ready、native exact clock 和零 overshoot。不会用内部 ACK 或顶层 `accepted` 代替实际后验。采集者已对 R203/R206 实际输入及未知 policy/overshoot 反例完成一次窄回放；本次整合复用该结果并核精确源码后像、AST、diff 与路径范围，没有重跑旧矩阵。

Root 在拍摄后另推进一日，终场 raw date 为 `53147424`：全场共两天，片中一天、后续一天分列。后续实际移动尚未抵达目标，也不构成 R06 ADD 因果样本。最终正常 Save 的 72,708,291B / SHA `0e2939864010b31d1fece183af3c0f058a248baf75ef16f33fba14eda438385d` 只引用原资格，不重新读取存档；CK3/bootstrap exit0，screen 正常释放、任务资源为空，OFF/clear 与关闭状态分别保留。a36 production-byte q 不是独立业务验收；原片尚无完整人工 1×、连续 clean 或 signoff。

公共 [first-managed INDEX](acceptance/2026-10-18-first-managed-common-runtime/INDEX.actual.json)已由 R205 更新为最新正常闭场的 R206 三份精确原件，供下一公共 allocate 的实际 latest-history 检查使用。此历史索引不是通用 fresh-admission 凭据：其他机器须重新核 machine ID、实际 runtime/版本/路径映射、容量与最新闭场；本机后续场次分配后也必须重新绑定，不能用 R206 绕过 latest guard。

下一步先采用正常 William 源与其身份，按公共单一 runtime 运行 R05 已隔离的目标绑定 initializer；原始查询跨 revision 只允许在同日期/身份约束下做至多一次只读 fresh 重取，不重发动作。R04 尚未抵达，R06 仍需 position=true、完整最终 shared-q>0 和同次 core/ADD 因果证据；R08 仍需真正 c/d writer→同次 NET→payer/cadence。研究 **9/14**、业务 **6/11**、合格动态 **0/11**、ABC **0/3** 均不增加。

2026-10-18 文档勘误：前版将 `1506→1513` 标作兵数，未有此字段来源支持；现移除该归类，不从这组数值推导兵员变化。原始实机与拍摄 RED、计数和代码不变。
