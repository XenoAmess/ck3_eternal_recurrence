# 麦加实际结果与88段制作输入

`machine_id: 4-8e1c2f1861`；本页观察截止 `2026-10-20T15:49:38Z`。仅记录本机本场，不外推其他机器或新局面。前轮朝圣及失败边界保留在[上一轮记录](production-b21-and-p3-20261020.md)。

## 麦加实验实际证明了什么

B22/R0013 的 Q21 骑士 reader 在游戏内可用。人物15893、10322同一暂停日期的总量分别为104%、129%，麦加named项均为+4%。对本信仰的麦加26只提交一次降级；独立后态确认eminent由true变false、虔诚4250→3250，完整十资源报价与实际付款均为1000虔诚。原确认ACK未自行授予业务成功，采用后续独立查询确认等级和付款。

即时独立后态的两人总量和named项均未变，`site_attribution_observed=false`，缓存刷新时间未证。本例可以展示真实零差分，不能据此断言降级无效，也不能把总量当作单座圣地贡献。源结果的`required_slots/E2-A1/closed=false`保持原样：[原adapter结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/live/4-8e1c2f1861--faith-engine--R0013/case-output/mecca26-knight-controlled-result.json)，SHA-256 `986f008c28c90061d75ba2868b09078593757becb9c6fefe47c1962fa3e860ce`。

随后一个自然日触发历史人物事件，第一显示项确有切换玩家效果；实际人物15893→41436。这段已混杂，不并入原人物刷新、钱包或属性后态。离线分析与下一场准备并行完成：[源码分析](knowledge/historical-char-creation-1-source-analysis.json)、[原生实例与独立后态](knowledge/r0013-historical-character-1-observation.json)。共享registry补齐1.20.0.4的九scope精确变体，复用既有第三项保持原人物策略；旧八scope与1.19记录保留。推荐第三项尚未实机执行。七项便携消费者通过，新消费者strict通过；四个生产模块仍有38项既有类型诊断，新增0项，不标为全模块strict通过。

两段原片各74.966秒，原录制job和probe均实际0；每段只审实际PTS5、35、70三帧。第一段仅确认报价画面，未授予拍到Confirm的信用；第二段先见3250，随后事件遮挡。两张原版PNG可用于报价与即时后态，最终换人截图不用于原人物比较。[媒体审阅](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/media-review-a01/REVIEW.actual.json)不授连续clean或完整人工听看信用。

退出采用原版GUI，保留句柄于15:29:56实际取得CK3 OS0；原host于15:30:01退出1，公共run原Popen退出0，两者分列。最后确认距离hold约227秒，未达到本轮自定300秒余量，不追认满足。Root在确认游戏和host退出后于15:48:51前写现keeper的STOP；keeper线程实际结束、无failure，原allocator于15:48:52退出0。屏幕释放及后继准入仍须引用实际CAS回执，不能由这些退出码推断。

## 制作与后续执行

最终选择为65条固定讲解、原B12装备1条和22条新案例，共88段；旧73段投影不作为新完整输入。当前A1三句旁白实际33.816秒，展示35.733秒，MP3完整解码与测长通过，尚未人工听审。[实际声音索引](C:/workspace/ck3-faith-and-power-20261017/episode02/case-voices-b25-a01/batch-a1-mecca3-a01/measured-narration.actual.json)已接入作者输入，保留前段“智慧之地外交”与新麦加骑士实验的明确过渡，不改65条固定声音。

原FormalInputs元数据验收已实际通过当前69段子集：65固定＋B12＋A1三句；必需结果槽2/24已绑定，22项待补，`content_ready=false`。这个比例是结果字段，不能当作影片制作百分比。当前仍只有70段24:33.600可播放预览；88段约28—29分钟属于编辑预算，尚未新渲染。

下一场优先补一次完整普通朝圣，分别验证出发、抵达、结算、活动终态和独立当前位置；不为固定事件ID或正奖励重刷。原生位置DTO仍未绑定，采用已有角色窗口与原版头像位置提示作独立视觉观察，方法单列。遗物个人装备／供奉两冷臂、普通／major完整双报价、同世界一次H2建制及H3只读状态并行准备。H1/H2新显式串联caller的7项消费者和修改范围strict检查通过，公共prepare与实机仍未执行。

容量修复只把录制服务整场上限896MiB改为2048MiB，raw512MiB、四段、总300秒及实际整场占用守卫保持；3项定向消费者和修改谓词类型检查通过，不是新录制资格。后继使用新的完整准入、当前源码绑定和公共prepare，不回写旧B23被896MiB限制拒绝的原失败。已有Q21 DLL继续沿用精确来源证明，不因离线Python改动重编原生矩阵。

## 2026-10-21 正常关闭勘误与后继截点

`machine_id: 4-8e1c2f1861`；本条于 `2026-10-20T17:02:48.402489+00:00` 读取已封小回执后追加，不替换上文历史截点。

R0013 最终 `normal-close-result.json` 的 `normal_close_qualified=true`，原生进程退出0与保留句柄退出0均已记录。此前场景摘要误将早期交接假设记为关闭合同未通过，现按[关闭勘误原件](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/SCENE-CLOSURE-CORRECTION.actual.json)纠正（2281 B，SHA-256 `2181217b4d4d13b5838a24d2670fb2d629c96fef642118146ee50aaabe89193d`）；[最终关闭结果](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b22-a01/live/4-8e1c2f1861--faith-engine--R0013/case-output/normal-close-result.json)为10728 B、SHA-256 `22723254a7be69d273d40c46e48493455858be8c74b64ccd034730b60c305003`。原host退出1、`business_pass=false`及早期canonical审图回执的`actual_os0_proven=false`保持原样；最终正常关闭不改变麦加收益归因未知或混杂段排除。

C10 `7bc3b62c5f01510db1eb74f1e2f13eb23eb0e7e7` 的[Official CI39452484280](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/39452484280)已在16:32:09Z实际读为失败：step53通过，step94的8项测试出现4个错误，原因是夹具的局部AST提取遗漏实际`advance_day`所需全局名称，触发`NameError: need`。远端runner的`machine_id: unknown`；本机读取记录见[CI终态](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/ROOT-C10-CI.a03.actual.json)。[外置test-only候选](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/ci-c10-step94-repair-a01/DELIVERY.actual.json)已实际完成8项、0跳过、原等待0及修改范围strict检查；尚未合入或取得新CI终态，不标为CI通过。

后继R0014仍在推进。已封小回执记录16:42:57Z一次Start调用、随后独立活动身份及同日金币243→173；70金是当前配置的活动费用，全程费用未证。[Start原回执](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b23-a01/live/4-8e1c2f1861--faith-engine--R0014/case-output/ordinary-pilgrimage-0014-receipt.json)、[独立钱包观察](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b23-a01/live/4-8e1c2f1861--faith-engine--R0014/case-output/ordinary-pilgrimage-post-start-wallet-observation.json)和[16:46:47Z旅程起始快照](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b23-a01/live/4-8e1c2f1861--faith-engine--R0014/case-output/faith-e02-journey-001-started-once.json)仅证明这个前缀；整趟朝圣、结算、归返、当前位置和特质经验尚未在本条验明，不借B20或B17独立世界补成连续旅程。当前执行与后续真实结果分别进入[10月21日日报](../../../../docs/autonomous-agent-progress/daily/2026-10-21.md)及[当次计划补录](../../../../docs/autonomous-agent-progress/meetings/daily/2026-10-21.md)。

## 2026-10-21 01:42 后继实况与修复

`machine_id: 4-8e1c2f1861`；本条观察截至2026-10-20T17:42:13Z。R0014在70个已证自然日后，day0119使用revision229，服务端实际为230，在Arm及推进提交前拒绝。原host随后以stop清理游戏，保留句柄退出1；不能记成自主崩溃或正常Quit。[实际闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b23-a01/SCENE-CLOSURE.actual.json)为5673 B、SHA-256 `c5b0d10fae55569a5a4f7bcb417d27f712c1c109b9b05bb63c8cafd9a2200021`：原run2、host1、allocator0、keeper正常停止，CAS12854空资源，正常关闭与业务均false。抵达罗马不构成结算或归返；本轮五事件全部离线分析并写入[来源绑定总表](knowledge/r0014-event-batch-summary.json)。

最小修复改为每次原生日推进前取得独立当前快照，继续传明确revision且只派发一次；未知结果不重试。刷新恰好看到事件时返回真实0小时边界，交回既有事件采集和第一显示项处理；不制造推进回执或一天成绩。P3预算显式计入新增只读调用。来源、定向消费者与类型检查见[修复交付](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/p3-r0014-day0119-diagnosis-a01/a02/DELIVERY.a02.actual.json)。

B28的首次公开预检另发现旧H1适配器缺少`verify_case`；它尚未分配现场或启动游戏。新增入口委派给已有严格单臂验证器，仍拒绝partial、unknown与跨run原件，且不授整产品业务通过。Root已按资格字节集成这些改动及test-only夹具修复，实际组合测试19项通过、原进程等待0；[组合回执](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/c11-root-integration-a01/COMBINED-ROOT-TARGETED.a02.actual.json)保留首次因缺测试导入路径而失败的调用与其后正确调用，二者不混计。新正式CI仍待提交后的实际终态。

制作端当前延续清单为[71段实际装配](C:/workspace/ck3-faith-and-power-20261017/episode02/final-authoring-b24-a01/CASE-BLOCKS.manifest.A1-P12-actual.a01.json)：65固定段、B12及5句新声共1486.933333秒，9/24必需槽已绑定、15待补、目标88段。P12两句实测24.533333秒；未执行新完整视频渲染，R0014未完成部分没有冒充完整旅程。

## 2026-10-21 02:24 普通圣地报价解析修复

`machine_id: 4-8e1c2f1861`；本条依据截至2026-10-20T18:23:43Z的已封原件。B28/R0015使用C11 `6d7b715edacf42c0849612a95ff543b2f3313c29`，正常关闭、原游戏保留句柄OS0、host/run/allocator退出0、keeper停止及CAS12868空资源均已取得；[实际闭场](C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b28-h1-ordinary-a01/SCENE-CLOSURE.actual.json)不能代替业务通过。H1结果仍为`PARTIAL`，错误为`Exact bounded integer required`，没有两份完整独立报价，也没有升格或创建领袖提交。

正式SDK的决议查询外层没有`capture_epoch`；独立原生采集序号在`selected_terms.capture_epoch`。H1两处消费者错误读取外层缺失字段，现按正式嵌套合同修复，保留严格整数边界、双方身份、同场绑定和两条独立query递增要求。[修复与实际定向验证](C:/workspace/ck3-faith-and-power-20261017/episode02/production-b21-a01/h1-verify-entry-fix-a01/nested-quote-epoch-a02/DELIVERY.actual.json)记录原009 SDK JSON进入真实消费者的优化模式单项验证通过、strict四源通过；缺第二份原始query仍拒绝完成。不修改SDK生产者，不重编Native，不将Select后观察冒充第二份query。

原009仅可证明本场一次完整十币种报价：300虔诚、225金币，其余八项为零；原生序号14094。当前Faith103确已采用纳杰夫32，关联边`eminent=false`表示普通等级，不能误读为未采用，其他Faith的等级不代入。本场[透明历史事实](C:/workspace/ck3-faith-and-power-20261017/episode02/h1-h2-composite-candidate-a01/narration-next-a01/B28-R0015-PARTIAL-FACTS.actual.json)不填H1完成槽。旧录制监看读文件时失败，唯一11.9秒补充片段仅为退出确认画面，不授报价上屏信用；后继使用独立场次及有界文件读取重试的新监看。
