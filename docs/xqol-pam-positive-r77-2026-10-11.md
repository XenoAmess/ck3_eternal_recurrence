# QOL PAM 正例 R77：启动资格失败与实际资源闭场

范围只含体验优化与重整河山的 CK3 1.20.0.4 迁移验收发布，不涉及361。2026-10-11 14:47 CST 记录：QOL 原业务矩阵仍2/6（33.3%，ordinary_async / pam_negative），重整河山0/2（0%），合计2/8（25%）；本轮两项发布均未完成。基础设施、计划、静态测试和资源闭场不计业务通过。

## 实际运行

公共 PAM+ a180/R77 于06:31:48.842542Z启动，06:37:08.120042Z结束，run exit2；随后仅一次公共 verify，exit2。没有重跑已消费的43 state。共同 Source19 runtime、prepared sibling 及35步/12自然日、command300/readiness400/timeout4500/hold600/poll0.05均沿用原件。Source19只修共享报告writer，不更换 native DLL 或业务合同；本场没有再次发生 WinError5 writer crash。

新鲜 Steam 窗口变化与两份独立 nonce 原图已由 root 直接审阅，均显示离线模式。普通实机未将 Steam 切为在线。

冻结 profile 的 `logs/debug.log:20470` 于14:35:46 CST发出 `ZQP120: TEST FAIL actual_positive_doctrines_landed_recipient`，来源 `zqp_pam_sample_effects.txt:126`；公共启动策略正确命中广义 forbidden `ZQP120: TEST FAIL`。宋帝 actor 资格在同日志12603已PASS，但双个人教义 setter 的 `free_personal_tenet_slots >= 2` 未满足：诊断为piety level4、free slots1，两项个人教义及其fulfillment flags均FALSE，未进入queue seed/D1业务。host保留 `RuntimeError: actual fixture qualification emitted a forbidden marker`，case NOT_RUN、case/gui/acceptance均false。

43实际 modifier 与sample均带UTF-8 BOM，并与原prepare及当前对应源码逐字节一致；Source19 sibling只改变顶层manifest绑定。`personal_tenet_slot_add = 1`是该游戏版stock有效键，但本场没有actor上 `has_character_modifier` 的真实回读，因此目前只证明设置后仍为一槽，尚不能确定是modifier未生效、缓存时序或其他原因。后继须新prepare并补最小真实诊断，不删双槽、双setter、forbidden或自然回复/精确奖励门禁。

## 资源闭场，不是业务通过

失败GUI退出后实际retained CK3 OS0，native zero proof仍null、normal_close_qualified=false；failure_shutdown_proof / failure_lifecycle_completed / cleanup_ok / managed_thread_finished均true，job0、进程清单空、control/watchdog均absent。仅自有Guard251在运行已终止后行政停止，实际monitor exit15；该非零值不冒充CK3退出码。keeper/allocator均实际exit0；屏幕CAS使用停止后最新序号，实际done/resources[]，seq8724。

小型post-run-only receipt直接调用三个公共closure谓词，均true；标准 `previous_session_closure` 已通过，不使用R76 unfinished-writer-crash的特殊入口：

- `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/pam_positive--a180/POST-RUN-FAILURE-CLOSE-01.json`，7084 B，SHA-256 `ee6ac156729f2491f5dbbf5d6b99946c6ed2b2a045aa3f7056f3414caebea1b4`。
- 原native report为23,924,202 B，SHA-256 `1ff40b240f99ad88f21574a371f557331a5ce6a6905d08b75d51cb0890249202`，原失败不改写。
- 原release回执 `C:/workspace/ck3-upgrade-20261006/resume-root-01/a180-screen-release-01.json`，SHA-256 `3b3250897864a724510ece64d23876e1b14fb51cfebf6c4b7189df934383c062`。
- 标准storage closer实际exit0，仅闭1GiB场次预约：`C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/pamplus-a180-source19-guard251-after-exact-reclaim-01-reservation-52-closed.json`，7843 B，SHA-256 `cb0d8de08c0124c6a96bea4bba0063abe7794d6523668cf0bd26bcf25923c719`。

Guard251实际基线union 3,555,336 B，最后观察净增长275,823,408 B，未触发750MiB/卷容量告警；这只是30秒采样净增高水位，不是所有瞬时写入的严格上界。闭账场次allocation280,152,032 B，项目保守usage36,553,772,656 B，整卷fresh available28,536,250,368 B；不把全卷变化归因为本场。

## 后继

并行继续PAM最小原因诊断、重整河山core开场准备，以及旧QOL R13–R17五根生成shadercache的用途替代复核。五根默认168h期限尚未到，不能称自动过期；其余原输入、SAVE、错误与业务证据保留至2026-10-18复核。任何回收只在新预约、精确根/单链接/ADS/占用/独占HANDLE核验后分批执行；候选789,999,600 B尚不是实际释放量。

优先在容量满足原2GiB估算后执行重整河山core。PAM+须修正并新prepare，再继续QOL两类任命及赎回。发布时间取决于剩余实机GREEN、正式tag staging、实际Workshop上传、匿名完整Change Notes回读、真实Steam缓存字节与加载及changelog master提交推送；当前不给未经验证的完成时刻。
