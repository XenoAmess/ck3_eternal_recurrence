# R0015：未启动游戏的闲置分配与修订素材收口

`machine_id: 4-8e1c2f1861`；整理 `2026-10-18T10:22:45.846358+00:00`。原始观察、失败和文件身份见[来源索引](evidence/faith-power-r0015-unused-allocation/source-pins.json)。本场来源fc4dc899，实际游戏仍1.20.0.4/build25734779，没有启动CK3或加载a09 DLL。

两方向公共prepare与plan均返回0。D1分配进入READY后，可视challenge抄读多次不符，始终没有绕过比较或读取JSON内容替代审图。Root与runtime对nearest衍生图也作过错误读数；回到完整原图后，由独立场景线程读出的32位串通过guard，新鲜原图Steam底栏可见离线模式。随后public preflight为0，但run为2：该分配已在10:08:27达到既有600秒unused idle截止，keeper实际正常停止并原wait为0，launcher因此拒绝。

本场没有host-started、launch-intent、CK3、native或control；这些缺失只支持没有开始游戏，不授正常游戏退出或业务成绩。现场实际于10:17:12.101552Z释放CAS11768。目标范围保留上界8,441,856B、future0，仍计入原D1预算，不再增加一个完整704MiB额度。

准备输入与一次性执行状态分开处理：READY已消费single-use-ledger，公共allocate正确拒绝同prepared重分配。后继须新unused state，复用母档及未变化来源；旧输入和本次失败不覆盖。原unused闭场读取器只认识旧场景多次命令与旧wrapper格式，本轮在既有入口补现代idle回执的窄分支，保留真实原始等待、唯一lease、无host／native及实际资源释放；不伪造旧scene证据，不改变600秒截止，不取得游戏资格。具体回归与只读实际验证见来源交付。

为降低同类读字错误，既有launcher将nonce显示改为当前Pillow支持的24px字体，banner最小宽度800、高度仍64；几何检查覆盖全部hex字符与相邻组合，原桌面帧像素原样粘贴，比较、nonce生成与时效不变。这是显示修复的源码与几何依据，后继仍须真正审阅新原图及通过guard。

并行媒体修订已经完成一条C09新配音和两张终态图。新音实测34.392秒，对齐34.6667秒，稳定132句总长2936秒；131声与130图继续精确复用。原producer在媒体完成后因font字段读取报exit1，第一次元数据后继又因未用import报exit1；第二次仅修元数据的后继实际exit0，没有重发TTS或重绘。Root直接看过两张原图，条件与人物方向可读；尚未检查最终focus／ASS像素或人工整片听审。XA／XB仍空，此长度不是最终影片长度。

通用方法与实际应用继续归入[制作经验](../../promo/ck3_faith_and_power/docs/production-experience.md)，避免把复用、局部修复或资源闭场当成实际玩法成功。下一门槛仍为新场真实hello、存档恢复、原版创建与采用许可和独立后态。
