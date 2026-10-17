# R200环境失败与R201移动前缀、事件和异常闭场

`machine_id: desktop-3fevhd2-1c74096080`；本包核对时间 `2026-10-17T17:08:51.449401+00:00`。实际R0201运行源及native构建源均为 `26449eb2676b4ccb71cb818fb0cc398b0a5fd1e6`，a34b DLL SHA `a9d66a039204308ecb0585863107b01b72df7bc0d609f2448263e369d6511da0`；CK3 1.20.0.4/EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。PID19896/create134367254052257145/gen1/episode `native-31254-c246d6a77712`，actor31254。主线后继源码不是本场部署事实。

## 实际前缀与失败边界

R200原775B stderr明确 `ModuleNotFoundError: No module named 'screen_bus_lease'`；Root观察为ENVIRONMENT_RED、bootstrap exit1、run目录未创建、游戏未启动，推进/录制均0。它是启动环境失败，不是游戏动作失败；旧启动没有重放。

R201从[R199正常S0](episode04-r199-refill-position-preparation-12004.md)独立冷载。actor停止回执只结算 **23个完整循环**，末date53148768、Army18在2633、arrived=false。另一次day24独立快照于2026-10-17T15:54:54.403093Z读到date53148792/paused=true、Army18仍2633/moving、目标2629，剩余route `[2627,2626,8753,2629]`。因此第24日已被独立观察，但不改写actor的23闭环数，也不授2629抵达或补员位置/ADD资格。

## 已知事件确认与独立后验

详细context识别 `pam_bull_events.0004`/instance2/calculated3850004，root31254、actor/bull_issuer30490；snapshot authored option_count2与实际只显示native0“就这样吧。”分别保留。知识查询available，原版file SHA `596a8f4ce0c9e64119b2e65917ec56f984c58882e5ccb0adbd2e56893d89f937`、node SHA `ebbdcde661d287de1ed8fe9e1cd8eb05343edf7ba3e84af883461e720f7eba5f`与[既有共享定义](pam-bull0004-notification-12004.md)一致。native0为空确认项；没有新事件策略或原版源码扫描。

Root一次选择option_number1/native0：ACK accepted/submitted，回执另证postcondition_verified及instance2→null；2026-10-17T16:11:24.085896Z独立snapshot再证active_event=null、paused=true、date53148792、Army18仍2633。窗口消失不授宗教、资源或军费效果。

## 异常闭场与后继决定

随后 `r201-army18-prepared-at2633-a01` 的ordinary_core_v1完整Army查询被Root报告超时，结果未知；本包只保留265B请求，不读大query、不补兵量/补员准备值。bootstrap原件记elapsed **1803.239s**、exit_reason=timeout、CK3 exit1、tree_gone/cleanup_proven=true、SDK线程结束，recorder NOT_STARTED。外层exit0仅为Root报告的清理结果，不能覆盖游戏exit1。

初始身份链确有date53148216的Save（SHA `898bcf6234c6a195840692574f63bbf4e3eab869112ad18c1b9f78e14492b62b`）；**没有推进后的正常闭场Save/正常退出，因此不产生新normal S0**。screen CAS6234→6235是expired-own-claim-released/resources[]，随后done6236；它只闭资源，不闭业务。

后继决定见[机器可读决定](evidence/episode04-r200-r201-movement-12004/continuation-decision.json)：新尝试从R199正常S0重新载入，目标先到中途2633并取得自动正常保存及正常闭场；不续用R201推进状态。R202实际身份/进度须独立记录。研究9/14、业务6/11、合格动态0/11、ABC0/3不变；无新录像、ADD或clean/1×/人审信用。

[便携小原件、局部字面投影与精确来源](evidence/episode04-r200-r201-movement-12004/README.md)可供视频核稿和agent恢复判断。跨机只复用知识与代码；Steam、容量、PID、SYSTEM及安装资格须在目标机器重新核验。
