# Episode04：R0174共同保存T0的21日驻地对照

2026-10-15，来源机器desktop-3fevhd2-1c74096080。R0174正常闭场后，现有portable pair checker实际PASS：同一正常保存T0的驻地分支完成21个精确自然日，Army18始终位于2624、route empty、target null，实际compact军力查询每日1196/1196；本分支未形成qualified boarding callback。

这补足的是**21日保存T0续行设计的无登船对照**。原R07卡仍部分闭合：历史处理组用了21天、跨真实经济结算窗口，T0已在移动；原卡要求的≤7日、避开结算、静止T0后新Move仍未满足。R01的指挥官和ABC合法目标完整冻结也未补齐。研究整卡不能因此从3/14擅自增加。generic钱包变化及空登船列表不证明零费用或维护费归因。

## 共同T0和独立窗口

共同输入为R0173的007正常保存生成的不可变seed：68451543B，SHA9ab3b0d05bdc1a0c4ef2d81a9dc27cec3f66e9af2871b5cac11776ddc6ddb784，raw date53145048（1066.10.15）。历史R0173先load R0172的be327...，正常保存成9ab3后直接续行；不能宣称历史处理组load了9ab3。

R0174从9ab3正常load；actor31254/history1128只属于其实际来源链。PID17468/createFILETIME134365505726865638/gen1/episode native-31254-0d067159706e，源码1463bd9b4b89612d283dd45ac4ec9efbf22f048d，a05 DLL SHA7929217c07ff4405445611558040cc282df98dcebc79d16f5a1b4e6bdc049b1b。游戏1.20.0.4/build25734779/EXE SHA98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518。

加载后独立snapshot、Army18完整ordinary来源引用、现金及admission匹配T0：progress31717/Q100000、actual loaded cutoff50000/Q100000、route[1036,8653,1034,1033]、兵数1196、supply30000000/Q100000、treasury25166043/Q100000。一条原版Halt提交ACK后首次snapshot仍可能是旧route；保留原提交/claim，只读再次查询才确证同2624空route。之后未重发该动作。

21日raw53145048→53145552，每日exact+24、tick1、overshoot0、独立暂停；natural_phase开启，其余8族OFF。payment window1/epoch1、natural终态retained42、payment latest15，消费者确认无覆盖/丢样。不同进程即使都叫window1/epoch1也不是同一epoch；本次没有跨窗拼接或相减sequence。day11婚姻通知按原政策拒绝，day15 bookmark.1070按实际第一项A继续（与处理组相同）；两天只读救回已执行的日步，manifest显式绑定原Arm和成功status/final，未重Arm/Resume。

## 可在另一机器重复的原件与代码

[便携包清单](evidence/episode04-r0174-20261015/bundle-index.json)、[原始JSON ZIP](evidence/episode04-r0174-20261015/r0174-original-json.zip)与[新便携manifest](evidence/episode04-r0174-20261015/pair.manifest.portable.json)保留231份精确原件，未重写其中原本的绝对来源路径。ZIP5051824B，展开108459029B，含baseline和21日的22份完整Driver sidecar；视频、存档、EXE/DLL及profile缓存均未复制。

处理组继续复用[既有R0173的18份归档](evidence/episode04-r0173-20261015/manifest.json)，不重复复制。重放器同时运行现有R0173生产消费者，重联一笔3金币natural boarding SUB，余额核销边界仍是whole original callback入口到返回；维护归因unclosed。两分支的observer来源版本不同且如实分别保留，不称两条新PID从相同新binary重放。

在已有项目Python依赖的仓库clone运行：

```text
python -B -X utf8 promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/replay_r0174_archive.py --work-dir <新的外置临时目录>
```

[重放器](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/replay_r0174_archive.py)先逐项核原始bytes/SHA；21个daily大sidecar仅流式核对而不落地，解出pair必需及small review项210份/18426238B，然后使用现有pair checker和相对manifest。原C/D来源字符串通过显式prefix映射到新archive root，不访问旧源盘；代码与依赖来自当前clone。不启动CK3、Steam、SDK或桌面。另一台机器的实际实机验收不会由归档PASS代替。

[真实相对重放结果](evidence/episode04-r0174-20261015/validation/relative-replay.actual.json)已PASS，现有pair checker和共享R0173 verifier都exit0。45秒驻地Halt原片属于独立媒体证据，未进这个文本包，clean span/最终主片剪辑资格另验；不能用本次21日窗口替原卡七日门槛。

## 模板pin修复与存储期限

原template误把外置CRLF且无末尾newline的13645B/SHA615a...用于Git LF投影。Git1463 canonical freeze实际13320B/SHA1d3593d906b8117934a8bb5cae6a1d3c6c280272c87476867f63e5e816362a5c。`.gitattributes`指定eol=lf；本修复只更新template的bytes/SHA，并加一项检查实际checked-in投影字节与T0内容的现有unittest。旧pin使该case真实失败，新pin真实通过。原ZIP/外置CRLF与失败历史保留，未为通过校验重写原件。

本轮操作准入和临时展开额度的真实截止是**2026-10-16T07:45:01.597000+00:00**，来自CAPACITY-ACCEPTED quota_review_at_utc；旧文档中的10月22日不授权延长。资料生命周期继续按通用存储策略复核，持久知识不把本机盘符和本次额度变成跨机器前提。
