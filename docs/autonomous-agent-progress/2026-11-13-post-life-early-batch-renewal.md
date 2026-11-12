# 已结算 Life 后提前续批（2026-11-13）

实际连续批次在 Life 已 SETTLE 后，剩余预算已少于既有 Life reserve，仍花数分钟重做 ROOT／行政发布／规划，最后才在原 pre-intent gate 退让。本单元在原周期完整结算、取得 fresh after-SEM 后，以同一个保留 reserve 提前正常结束当前批次。真实连续 Root 随即建立新 batch／新 request，下一批仍完整观察和选择小动作；原 Life、命令期限、horizon、年度 SAVE 与守卫不变。

该行为需要显式 scheduling opt-in：旧六参 BatchLimits 和通用 Control 默认 false，实际连续 Main 声明允许，最后可用 batch sequence 不准入。Controller 只在真正 Life handler 的 APPLIED／visible／eligible 结算、无 pending／UNKNOWN／UI／writer 异常、同 Game／actor／episode 的 fresh SAFE／paused／map-ready ending、物理 savedPair 存在且未达 8760 ticks 时准入。turn bound 与 STOP 保留原先顺序。只有已经证明不需要 SAVE 的这一出口跳过重复 dirty-tail Ready；缺基线、年到期、资格不明与保存后续仍走旧路径。

提前出口复用原 WALL_TIMEOUT → BATCH_DEFERRED → Root clean-wall continue，保留已完成 cycle 的信用，不发新 INTENT、不重做原动作。原 reserve 的 floor、历史 estimate 与 subject 规则不改，不用新批次延长旧命令。

## 有限验证与来源

actual coherent 四 TU 首次编译完整35类（Controller19／BatchLimits1／Loop11／Main4）。owner20 测试用真实 Controller／OrdinaryPlanner／RootLoop.BatchAccess 和共享 Clock，公开 Life／children DTO 经实际 ActionEffects 与 child bindings 校验。检查型 BatchJournal 验证所捕获 SEM／原 receipt，并经真实 retain → fresh after-SEM → settle；它是软件 DATA fixture，不发行私有 canonical authority。

正例核实第一次退让前只有原 planning 和 after-SEM 两次观察，无重复 tail／policy，原周期先结算，journal 结束后才回调并进入下一批；下一批确实执行新的小动作，新 request 有独立 deadline，原 Life bytes／deadline 不变。旧六参、默认 Control、turn bound、STOP、缺物理基线与原 SAVE readiness 拒绝均保留。首轮3P1F是测试误判缺基线旧 SaveRound 路径；仅修其预期和控制型 readiness 拒绝后整4P，生产未改。最后仅将年度 case 从 maximumTurns=1 改为2，实际在1个 completed turn 后仍有下一 turn，确保覆盖新 helper 的年度排除；同四项再次全部通过，生产未变。旧稿4P仅授 turn-bound tail 的事实保留。

formal Controller／BatchLimits／Loop 的 BASE 与候选均与 actual 逐字相同。formal Main 保留原入口未含 Runtime 专用 runWithHost／bindOrdinaryHost 的差异，只加 scheduling opt-in 方法；正式资格按实际依赖单独核，不凭 source 相似授全 Root。

完整源在 J/post-life-early-renewal-source71/SOURCE-READY71.json（5358B／2da2becbc6b8d7a46c61b2a591601e87f651fac4b7cae649aa90e2fdc7f78aae）；正式变体 SOURCE-READY71-FORMAL01.json（4091B／249360cff0f4051003552435fff0071b5a6b6eea174e6baa3545d6d678fdc991）。J 为 D:/ck3-state/resume91-java-delivery/ordinary-p0-20261108/life-postcondition-p0-20261112-01。必要编测原件在 F/postlife-renewal71-compile01、F/postlife-renewal71-whole4-junit01／02／03；F 为 D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01。原3P1F与全部输入保存。

两个模型完整生产答复保留：首 NO 误读 clean-wall／turns，唯一纠错有未限定 Run receiver、资格与 turn-bound 顺序等缺口。最终部分采用 BatchLimits 新组件＋旧六参 false constructor 和 RootLoop 七参调用形状；实际 owner 完成 Run helper、完整资格、Control／Main opt-in、sequence 与 tail 出口。未原样采用模型 Controller，不把静态缺口称实际编译 RED。并行模型测试草稿未应用，实际测试由 owner20 完成。

本单元与已过差分的 Source69 私有 encoder 一起交运行岗选择原 C65 清洁边界。源码／软件通过不等于已装载、实际提前退让、SAVE 或性能目标；私有 Main canonical capture、真实 writer 发行与 live 行为另按回执确认。当前仍未达到10秒／新增确认保存日。

最终 actual whole4 原件：F/postlife-renewal71-whole4-junit03，2026-11-12T18:57:49.841071Z CLOSE released；Jupiter48727B／e7d17285441940fdd490bf3c6057a49f5857bc10627a6f94f7d6bac04202ff58，POST1516B／0be05835c89ae49434fe6cab2f003d4a6e19792f1565e2784bc9f322b3b76f75。formal 四TU独立首0／35类，复用同一最终 Test12 对正式产物独立 whole4P：F/postlife-renewal71-formal-compile01／formal-whole4-junit01，2026-11-12T19:03:17.257540Z CLOSE released；Jupiter48661B／0b3a9030d25b45e81c14c88825606be54324e9fa4e5fe40057acfede92882853。未重复编译测试，未外推私有 Main issuer 或全平台。

## 后到实际采用及首自然提前续批

machine_id：`xenoamess-full-tower-eb9d2c1186`。运行岗在原 C65 完整收尾后，以一次五叶 normal fullreload 一致采用69＋71；同 host161132／原 birth、同 Game145132／keeper56732保持，新委托 cce3454f／restart2 于2026-11-12T19:38:04.2614466Z真实 LOOP。五个 Maven top.class均与软件合格原件逐字节／SHA一致，未做cold启动或重放原动作。

STOP→LOOP完整438.6166586秒，包含121.1270404秒GET及61.768秒augment WARN；新窗起点480observed／463eligible／373saved，0新增SAVE。原件 `R/attempt69/ACTUAL-LOOP-COHERENT69-71-AND-FULL-HANDOFF-COST01.json`（5505B／704f47c7ccb7cbc777e18e23af1db7e0a094eb937384592683cfb825fa154068），R为D:/ck3-state/resume91-runtime/quarkus-dev307-runtime。

首新 C66 于20:02:23.0783011Z实际SETTLE，488observed／471eligible／373saved；batch55 report实为WALL_TIMEOUT，detail为POST_SETTLE_LIFE_BUDGET_DEFERRED，剩344.6079997秒小于原reserve1033.7493942秒。实际Root沿BATCH_DEFERRED进入batch56，20:02:32.7951394Z开始，距SETTLE9.7168383秒；无新GET／STOP／提前SAVE。这已证明新提前续批正分支及实际连续消费者命中，未授私有encoder单独贡献或因果速度。

该report完整墙钟1456.6101694秒、ACTION1028.6855487秒，OBS172.1049409秒、PLAN158.4749803秒、JOURNAL87.6126642秒；nested阶段不相加当CPU。原件 `R/attempt69/BATCH55-FIRST-POSTLIFE-RENEWAL.original.json`（50053B／dd13f600d9de917185069846e337953b2a1d3d82cbfd5513efdf6df3d0a8015f）。旧Source68完整窗保留10658.401408秒／39新增eligible且0新增SAVE，不用不同周期做严格A/B或以eligible替代新增保存分母；当前10秒目标仍未达到。
