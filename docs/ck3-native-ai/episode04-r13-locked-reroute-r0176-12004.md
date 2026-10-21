# 1.20.0.4：R0176 锁定首段重新下达路线的实际后果

R13 的独立正常载入从 Province1036、date53146320 的静止 Army18 开始。一次普通 typed Move 到1033形成 `[8653,1034,1033]`。date53146440实际进度95108严格大于加载阈值50000，首段剩余25714；fresh preview 给出通往8645的 `[8653,8645]`，一次 typed alternate Move 保留首段及进度、替换后缀。独立原生帧确认先到原front8653，再实际到alternate8645，最终为空路线。重下命令至终点实际8天，完整baseline至终点13天/9个自然clock代际。

来源机器 `desktop-3fevhd2-1c74096080`；R0176 PID4992/create134365619855039955、generation1、actor31254、Army full ID18、episode `native-31254-ab05e6628183`；源码 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。原final report观察时间2026-10-15T18:38:48.378421+00:00，来源及精确pins在[便携验收](acceptance/2026-10-16-episode04-r13-r0176/README.md)。这些实际事实只授予来源机器当次会话。

共享 [replay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/replay.py) 增加R13入口，复用R0175归档读取器、生产 `verify.frame/r13` 与固定源码SHA的clock validator定义。六个完整关键查询、实际请求/响应、全部9代clock通过离线重放；四个新R13变体拒收。保留真实三天burst与提前Army/route停止，不伪造严格单日manifest。R0175矩阵未重跑，代码没有改动游戏或主树。

录像与业务后果分别保留：原raw为45s、60656946B，SHA `e8eccb2e36b143a94ee73f6f481a792d79adc55df9e387ad1284ef3216c40535`，身份只复用exact recording closure JSON，未读/重哈希视频。Root观察到alternate实际到达在69.53s，位于片外，因此不给终点镜头信用。连续clean和最终humanapproval仍为false。

本包只收已结束R13阶段的exact refs，没有R09响应或未来CLOSED。录制pipeline结束不等于游戏、SDK或现场已闭场；完整闭场待独立补充。拆合军及其后置不由R13结果外推。代码和机制可跨机复用，安装/部署/进程状态不能跨机继承。

外置lane上限8MiB、metadata256KiB，计既有active32MiB/metadata17MiB；原保护/复核截止2026-10-16T07:45:01.597Z不延长。

## 2026-10-21追加：限定三态源镜头正式签出

来源机器仍为`desktop-3fevhd2-1c74096080`。[Root于2026-10-21T02:23:09Z的实际裁定](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r0176-r13-positive-review-a01/ROOT-R0176-R13-FORMAL-ADJUDICATION.actual-a01.json)（4850B，SHA-256 `cbfcdfdffb377a3aec38ee256ec88b0b122eb28a7e78c6203f6dc7630fcb9d03`）接受同一原片的`[0,30)`秒/900帧，30fps、time base 1/1000、末选定PTS为29.967秒。只授原M165要求的“操作前旧路线→新命令即时路线→首段完成后新方向”，正式动态由7/11增至8/11；R05/R08/R10待，研究10/14、业务7/11、B0/2、ABC0/3不变。原M163仍要求原生完整后果；其最终8645到达已由保留原生回执独立确认，未以片内镜头替代。

本次一次有界提取产生57张联系表/900实际连续格，原FFmpeg PID18000的原Popen wait0，实际PTS/order与lossless gzip CRC均通过。AI代理逐张实际看全57张；Root代理另看000/007/018/037/056五张（68个有效格）及原样本00/01/02/03（0/4/10/20秒）。缩略格无阻挡必要路线的桌面、外部窗口或modal；不声称900格全部原分辨小字可读，也不是人工1×或Root逐900帧审阅。末张只有896..899四帧有效，12格黑padding不是源黑帧；30秒和43.5秒两个旧样本在选段之外。

原样本只将后缀变化夹在`(4,10]`秒、首段后位置/方向变化夹在`(10,20]`秒；原生事件精确encoded PTS为null。旧路线远端有部分在视野外，且新目标最终到达不在45秒原片内。历史69.53秒与另一路65.6104秒均为不同墙钟观察，不倒算成PTS；暂停GUI日期不证明完整13自然日，9代clock/13日仍来自独立原生证据。

Root本次独立完整SHA读回与原raw保留pin一致；媒体作者未重hash、未新probe、未重跑1350帧整片QA、未复制raw或渲染影片。新连续clean只覆盖选定900缩略格与具名原样本，旧段的当时continuous-clean=false、终点片外以及历史完整闭场pending均保留，不追认旧cleanup。新Root裁定明确原件继续用于正式镜头/最终剪辑，有限复核到2026-10-22T02:30:00Z，不给其他旧资产自动续期。完整R13变体、整片、人工观看和最终交付均未因此完成。
