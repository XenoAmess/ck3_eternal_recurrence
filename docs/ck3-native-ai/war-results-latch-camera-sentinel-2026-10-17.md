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

## 2026-10-18 01:27 CST补录：关闭期间暂停改变与SDK49接续

本节按10月17日UTC原件在次日补录，不代表零点已经知道结果。[有限来源及实际字段投影](evidence/p49-war-results-scope-pause.json)保留失败与恢复的不同信用。

SDK47窗口14在510日后停止：FULL750／AUTO781于16:16:18.626413Z完成Native关闭回调，但同raw53314512的暂停状态由true变false，返回verification_pending／accepted=false／UI信用0。旧classifier只认旧reason及scope_unchanged，因合同变化拒绝；后续SEM782已到53317032、unpaused且event69存在，额外105日为无人计时漂移，不计稳定、日期或业务信用。原781关闭结果仍未知，动作不重放；暂停控制783在env缺N时发送前失败，也不写成成功暂停。

公共Service只在既有战果关闭返回后增加六行调用；新helper要求精确的完整回调、同日期暂停翻转原因及source／owner合同，先读当前语义帧，必要时仅调用现有pause-map，再独立读回同owner／actor／episode／connection与非倒退版本、日期的暂停地图。它只发布paused_same_owner_requery_required观察，不能替代新窗口查询或授予原关闭成功。暂停失败、后态未知或错owner继续保留pending；原命令不重发。另提取[纯结果资格函数](../../tools/g2_saved_campaign/war_results_scope_transition_outcome.py)和[最小历史classifier差分](evidence/p48-scope-transition-classifier-research.patch)，不复制完整canonical，也不声称所有公共runner已接入该API。

23项定向／回归测试及11个子例通过。真实Service.auto_turn经过实际NativeDriver构造器、关闭transport、execute_step／primitive与history；仅Native输入及预选初始plan为替身。规划public870与wire Native7550明确不同，关闭请求绑7550、随后暂停绑7551。105日中途漂移、暂停失败和新connection9为明确合成变形；旧connection8的执行闩锁不得跨connection退休，独立新查询不补旧动作信用。原作者仅helper或构造绕过测试与此链分别记录，未冒充实机重放。

SDK48已通过正式parser与Native构造器，却在RT配置驻守speed5时拒绝route4＋AB：stationary-objective A/B requires route/contact speed 3。queue／app均exit1，尚无MCP工具／Game动作。4218的参数透传本身不等于这组联合配置兼容；SDK49改回route3／AB false＋既有hold5。今后验证必须走完整正式入口的parser→factory／constructor→全部RT configure→Service／server注册；不能只凭parser通过声称可启动。

SDK49原CAP2的Native结果保留，派生治理metadata误加machine_id造成校验失败，UI3亦在发送前失败；control4仅本地重消费原CAP并使用有披露的纠正副本，0MCP、不重放。随后独立UI5在connection10／ticket7869确认hidden，仍无781关闭信用。AUTO15真实选择event69的option2并获event_instance_advanced后验；AUTO23／MET24真实+7日，SEM35／MET36为cycles5072、raw53317368、paused／map-ready匹配。本代从53317032累计健康14日，Root准入c9ac56d0开启窗口15（baseline53317368，firstFULL37）。后来固定Root截点raw53318640，是本代累计67日、该窗口53日，不混用分母。同Game51028和5ebe录像未重启；这些是固定健康前缀，不保证未来持续运行，也不授新helper未来同故障分支实机验收。

event69的stress_threshold.2202随后经batch0037离线分析发布；Root对原冻结before69用已部署loader复用，status=offline-source-reviewed、binding_mode=exact、reused_known=true，原件未变，0MCP。该来源已知证明发生在实际选择之后，不倒推早先选择已用已知策略；registry_contract_accepted与material_effects_verified仍false，不称语义最优或增加G2信用。

[SDK47已封318日样本](evidence/p47-stationary-performance-318d.json)为479.490396秒，即1.507831秒／日，固定4702–4941周期；不是全战役均速，嵌套stage不能相加。后续[SDK49固定5104–5165](evidence/p49-settled-performance.json)已由ad04a15e最终封包：118日／134.924610秒＝1.143429秒／日，含62轮、43零日、1次SAVE、4.413361秒内部gap；此前166.180383秒交接gap不在该连续片段内，较宽157日样本含两个gap为2.999473秒／日。[stage并集](evidence/p49-stage-slice.json)把82个递归plan累计42.765141秒纠正为62个区间的29.275382秒独立wall，其中已观察Native wait0.998858秒、snapshot2.611838秒；余量不等于Python CPU，不与外层时长相加。该报告无生产补丁或活状态读取。

695提交56527e80的Official39048607827／Linear39048607848与MCP提交4218ab38的Official39049025056／Linear39049025059均SUCCESS；旧RED保留。本批不操作Game／MCP／OBS、不读实时Driver／SAVE／媒体，不重编Native。用户随后要求度假温和收尾，Root在最终SAVE652前置竞态后准备653原位恢复，不再开FULL；最终闭场见[度假交接](../handover/2026-10-18-robert30-clean-vacation-handoff.md)，不把上述健康前缀继续写成实时running。目标仍稳定30年，再<1秒／日、0.5秒／日；均未达，G2仍6/8，自然继承未验收。

最终Root eb0cb9f9已封：窗口15 repair_required573日，653新SAVE真实物化、cycles5364／raw53331120不变，旧6520dispatch／不重放、无窗口16。SDK双正常0／0及录像／辅助进程收尾，Game一次WM_CLOSE未退、无force，原supervisor／keeper保留；后WM_CLOSE没有fresh SEM，不借先前656称当前地图已验证。EDL仅封存、有历史open wait勘误未整链，无渲染。park指针20e4846d和最新SAVE／Driver seal／存储期限／接手顺序见上述交接。
