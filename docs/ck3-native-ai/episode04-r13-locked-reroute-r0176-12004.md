# 1.20.0.4：R0176 锁定首段重新下达路线的实际后果

R13 的独立正常载入从 Province1036、date53146320 的静止 Army18 开始。一次普通 typed Move 到1033形成 `[8653,1034,1033]`。date53146440实际进度95108严格大于加载阈值50000，首段剩余25714；fresh preview 给出通往8645的 `[8653,8645]`，一次 typed alternate Move 保留首段及进度、替换后缀。独立原生帧确认先到原front8653，再实际到alternate8645，最终为空路线。重下命令至终点实际8天，完整baseline至终点13天/9个自然clock代际。

来源机器 `desktop-3fevhd2-1c74096080`；R0176 PID4992/create134365619855039955、generation1、actor31254、Army full ID18、episode `native-31254-ab05e6628183`；源码 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。原final report观察时间2026-10-15T18:38:48.378421+00:00，来源及精确pins在[便携验收](acceptance/2026-10-16-episode04-r13-r0176/README.md)。这些实际事实只授予来源机器当次会话。

共享 [replay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/replay.py) 增加R13入口，复用R0175归档读取器、生产 `verify.frame/r13` 与固定源码SHA的clock validator定义。六个完整关键查询、实际请求/响应、全部9代clock通过离线重放；四个新R13变体拒收。保留真实三天burst与提前Army/route停止，不伪造严格单日manifest。R0175矩阵未重跑，代码没有改动游戏或主树。

录像与业务后果分别保留：原raw为45s、60656946B，SHA `e8eccb2e36b143a94ee73f6f481a792d79adc55df9e387ad1284ef3216c40535`，身份只复用exact recording closure JSON，未读/重哈希视频。Root观察到alternate实际到达在69.53s，位于片外，因此不给终点镜头信用。连续clean和最终humanapproval仍为false。

本包只收已结束R13阶段的exact refs，没有R09响应或未来CLOSED。录制pipeline结束不等于游戏、SDK或现场已闭场；完整闭场待独立补充。拆合军及其后置不由R13结果外推。代码和机制可跨机复用，安装/部署/进程状态不能跨机继承。

外置lane上限8MiB、metadata256KiB，计既有active32MiB/metadata17MiB；原保护/复核截止2026-10-16T07:45:01.597Z不延长。
