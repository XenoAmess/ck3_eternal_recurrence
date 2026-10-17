# 战果关闭闩锁与镜头阈值哨兵：公共源码修复

`machine_id: xenoamess-full-tower-eb9d2c1186`。本批基于公共 `441938d9`，只收两项已冻结候选及必要测试、有限证据。运行中的Native25、SDK、Game与录像均未由本批修改；不授战果窗口修复或镜头修复的实机信用。

## 战果窗口的完整回调与后续独立查询

历史P41 AUTO814的关闭回调在ticket845返回，AUTO816的独立查询在ticket846确认窗口隐藏，但旧执行闩锁仍保留。离线在该真实形状上构造未来 fresh-visible 查询，可确定性触发普通规划器的 pending 阻塞。未来可见场景与scope-transition变形是明确的合成案例，不能记为新实机观察。

修复只归档原回调已完整返回、无dismiss异常、不可继续收取的 `verification_pending` 执行记录。后续查询必须通过原正式合同，保持同owner／actor／episode／connection，日期和原生版本不倒退，ticket及GUI pump严格更新、线程一致。旧 `callback_pending` 谓词不变，既有scope-transition分支保持兼容；`state_changed`、未知、未返回或错误scope仍保留 pending。

归档记录明确为 `callback_completed_closure_unverified`，原动作不重放、关闭信用0。后查 absent／hidden无需关闭；新帧确认visible可建立新当前意图；同帧visible延后，避免零日close／query循环。此修复不把“回调执行结束”改写成“窗口已关”。本批只有两处生产叶窄改，没有复制整个SDK或canonical classifier。

公共正常导入测试为10个新方法，连同既有scope／priority／首读失败／startup回归共38项、6 subtests通过。私包的第11项是可选旧冻结源回放，公共测试不依赖外置旧SDK或动态候选loader；原始失败与来源pins留在清单。测试执行真实transport／normalizer／普通planner，Native I/O为替身，不声称完整实机auto链被重新执行。

## 原版镜头阈值表中的合法 `-1`

[原版表小投影](evidence/native-camera-vanilla-sentinel-table-2026-10-17.json)记录 `TITLE_ZOOM_LEVEL_EXTENTS={1000,800,600,400,300,200,100,-1}`，来源为实际原版文件及SHA／行号。Native25的 `NativeBucket` 原校验拒绝全部负数，因此整张合法表在读取zoom index前即被拒绝。唯一生产修改为 `<0` 改成 `<-1`；原非负extent、表长、单调顺序及viewport守卫保留。此前镜头失败没有分阶段原生诊断，不能据此断言实际请求已经通过所有更早守卫。

公共既有 `xar_ck3_realm_camera_geometry_v1_test` 增加18个实际表／原版bucket对应与6个守卫案例，无新EXE目标。完整公共test.cpp通过极薄export wrapper编为离线DLL，真实MSVC `/W4 /WX`验证：旧头文件下返回8，新头文件下返回0，24个新增检查和原几何／wire main均通过，见[公共焦点回执](evidence/native-camera-sentinel-public-fixture-2026-10-17.json)。[原冻结夹具](evidence/native-camera-sentinel-original-fixture-2026-10-17.json)的18个旧RED及24项新检查保留。本轮未运行完整CMake目标、未重链Game桥接DLL；后续真实采用仍需重编实际camera consumer并重新核include／link来源。像素覆盖、摄像机真实生效与coverage_verified均未授格。

## CI更正及当前失败边界

公共 `44ffae7c` 的[Official39039155294](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39039155294)终态为FAILURE；Family／overview来源测试步骤已通过，失败在共享验收中的旧managed UI断言：它仍要求精确`.4` Character路径一律army-only，但先前外部源码已开放该typed路径，旧army回执实际被 `window_kind` 绑定拒绝。[原RED小记录](evidence/sdk44-ci-failure-39039155294.json)保留。

远端 `441938d9` 已修正该测试，分别验证旧`.3`及未支持操作在发送前拒绝，精确`.4` Character请求经同一managed绑定发送一次并保留verification_pending；本地6项通过。本lane没有放松生产合同或另改该外部测试；线性接入时保留外部 `4531c4dd` 的县关系证据。原44ff CI不改写为成功，后继提交另行验收。

Root于14:15 UTC纠正现场截点：SDK44窗口11在推进143日后，FULL416／AUTO453于14:06:15.252605Z报move-army167772577→2621 `state is unavailable`，期望Native6285；cycles4365、raw53297328。错误不能推断确定未提交，原453不重放。此前planned45仅file-only且从未执行，现已撤回；实际修复由Root／fresh／finalHop另行准备。本公共候选不冒充已部署的SDK45，也不把窗口11继续写作运行中。

## 有限性能与policy-defer实测

[P44固定77日小报告](evidence/p44-settled-performance-and-cadence-2026-10-17.json)记录已完成4198–4347：MET到MET为498.764377秒／77日，即6.477459秒／日；首AUTO到末MET为6.441535秒／日，不是全战役平均。嵌套stage、分类时长、SAVE和wall不能相加。

同报告确认两战的逐战policy defer已在AUTO59实际出现，到期AUTO81／83重查；早期EVENT30／32合法重置否定计数。这只证明既有policy已生效，不是新的Native否定、业务动作或相对基线提速证明。Commander查询因当前scope缺current commander ID，不能安全凭纯SDK冷却保证即时失效，本轮不实施该建议。Army private scalar在该P44样本仍off，不转移旧Game的AB证书。

稳定30年优先，其后小于1秒／日，再0.5秒／日；均未达成，G2仍6/8。完整公共文件和候选来源见[来源清单](evidence/results-latch-camera-public-transplant.json)，不纳Driver、SAVE、原片、Game DLL或完整历史。
