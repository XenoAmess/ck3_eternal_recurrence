# SDK43：未知到达时间下的原地防御观察

本批在 `xenoamess-full-tower-eb9d2c1186` 收口必要源码和小证据。目标仍是连续稳定30年，其后低于1秒／日，再到0.5秒／日；本批均不授完成。公开移植不修改正在运行的 SDK、Game、录制或冻结源码。

## 原地防御单日退路

P42 AUTO557 的完整同帧路线查询得到 typed `timeline_unavailable`，AUTO559 因没有安全路线停止，窗口9保留失败302日。Native 对所有参战战争收集完整、去重且未撤退的敌军集合，要求请求集合精确相同；任何一军时间线读取失败都会使完整结果不可用。逐敌拆查不能取得等价的接敌安全证明，原错误也没有发布具体失败角色／军队。[原生完整范围来源](evidence/p43-native-complete-hostile-scope.json)单独保留。

新增策略仅在一支我方可控、陆地 regular、非战斗／非撤退、无既有移动的军队驻守时使用：所有既有精确出口已拒绝、当前省存在敌方威胁、完整敌军同帧查询确实返回精确 timeline 错误，且现有单日 Native 哨兵／暂停能力齐备。它选择既有 `life-advance-one-day`，随后重新观察。`contact_free_proven=False`、接敌或战败可能、无移动重发、无主动攻击授权、无战果或物质信用均明确保留；1.5主动战斗门槛不变。

SDK43 已实际同 Game 热接。AUTO16 选择新 phase，原生时钟从53263296推进到53263320、实际暂停，MET17独立匹配；随后AUTO22／28／34／40又各推进一日。这里实际记录的速度为5，单日截止来自原生哨兵，而非把未知 ETA 改成 available。以上只证明这些日期及暂停读回，不证明日内无接敌或防御策略最优。[实际字段投影](evidence/p43-actual-defensive-day-and-followup.json)保存原响应 SHA；Root交付截点窗口10曾推进97日，不是持续30年成绩或本文的实时状态。

普通公共 chooser 回放保留实际SEM560、CAP2和已完成查询DTO；早期历史索引及命令行包装明确为重构，不称完整 Driver／Service 重放。另有17个拒绝变形，覆盖弹窗、移动、战斗、敌军集合、日期、原生错误、lease和能力缺口。

## 每场战争的终战查询节奏

每场战争在两个不同日期取得合格且没有可执行胜利／可接受白和平结果的原生查询后，可按策略延后再次查询，最多30游戏日。角色、episode、connection、参战集合或战争角色改变，终战提交／交互边界、失败查询、已知胜败阈值及已知CB时长门槛均使延后失效；驻守截止也不能越过延后到期日。

返回值明确是 `policy_deferred_after_two_no_action_queries`，不是当前 Native negative、合法和约、动作成功或业务信用。记录保留上次CB完整身份；廉价当前SEM未发布当前CB身份时仍为unknown，不能把旧身份当作当前原生许可。任何实际终战动作继续需要原生读取与原有合法性检查。

P41固定区间的155次历史查询在[条件反事实](evidence/p41-termination-cadence-counterfactual.json)中变为36次查询／119次策略延后；原查询59.47秒只构成该模型的耗时上限，不是SDK43实测收益。P42已结算302日实测全段1.505秒／日、首AUTO至末MET1.206秒／日；其中89.766秒长间隙未归因，不能任选较快口径称达到目标。[历史测量](evidence/p42-settled-performance-3039-3299.json)保留范围。现 `ordinary_core_v1` 仍读取完整Army范围和丰富字段；小MET记录约23.13MB，未打开大payload就不排序其字段占比。[源级边界](evidence/p42-army-source-boundary.json)不构成提速部署。

## 镜头、启动与录制边界

普通Native镜头路径的排队ACK现在标pending；只有实际 Native `settled` 且后验验证为真才标完成。原生unavailable／partial保留失败与 `available=False`。同一失败序号只开启一次30游戏日冷却，不滑移、不记住未提交的新目标；到期允许一次重试，普通玩法不等待镜头。它修正状态及节奏，不证明镜头移动、地图覆盖或原生故障已修。

SDK43首owner因自动review不满足既有Root-only合同而失败。第二次使用Root真实地图／overlay审阅回执，建立独立owner记录和日志，未放松原guard、未改写第一次失败。完整最小改错及被撤回的自动准入边界见[启动研究配方](research/p43-root-reviewed-startup/README.md)。

旧录像7c2d在预览PNG替换时发生WinError5，已验证owned OBS正常退出与录制失败分开记录；新5ebe实际开始，局部SDK附接的missing-module失败也保留。约27.982秒的muxer间隙是墙钟证据，尚非最终PTS。preview-safe实现属于独立promo工具链的未来恢复候选；当前5ebe旧worker没有热改，不能写成该候选实机通过。[录制小事实](evidence/p43-recording-recovery-facts.json)不包含视频正文、编码或像素终审。

## 同源事件、实际损失及验证

负数交互的采集、原生拒绝、旧worker分析发布与当前loader的source-known读取已实际闭合；新实例仍使用自己的原生句柄，不复用旧负数ID。[学习报告](p42-signed-interaction-learning-audit-2026-10-17.md)不授最优语义或教义收益。

本局AUTO193选授独立后，战争数2→0、held集合5→3，失去2196和2200；这不是两场防御胜利。[首次进攻当时取得2200](p41-first-war-expansion-and-offline-learning-evidence-2026-10-17.md)的历史事实保留，不能声称当前仍持有。已知拒绝hook曾锁旧计算ID；公共单叶现按当前ID重算同一原版源码和完整目录的exact指纹，保留Native／Game／frame／角色／可见选项守卫。unknown兜底不改，拒绝仍可能引发派系战，不称无条件最优；此单叶未写入当前SDK43。[实际损失和候选边界](p43-populist-current-source-and-natural-audit-2026-10-17.md)分开记录，G2仍6/8。

本公共移植共49项聚焦测试通过，另含现有变形子例；镜头测试调用真实公共worker和Service方法，只替换Native presentation I/O。只把这些文件接入既有离线CI步骤，不新增全矩阵或实机门禁。启动人工review及运行端owner属于历史研究配方，不冒充公共自动准入API。

[公共源码／测试Git blob及外置原始交付身份](evidence/sdk43-public-transplant.json)分开记录；未将SDK整叶、Driver、存档、视频或原始大trace入库。
