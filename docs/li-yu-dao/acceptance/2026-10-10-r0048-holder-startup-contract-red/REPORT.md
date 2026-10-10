# R0048：启动证明合同失败，尚未执行授封诊断

2026-10-10 09:19 UTC，实际 Source09 host 在取得 D2a 存档原生帧后拒绝 holder adapter 返回的启动证明。公共 run / verify 实际 exit 2；未提交事件选项、未 SAVE，也没有前后继承名单或正常 GUI 退出资格。不能据本场判断继承缓存变化或图形缓存命中。[实际事实](FACTS.actual.json)。

原因已由本场实际 snapshot / event packet 和 Source09 完整证明校验函数离线重现：host 要求外层仅有 expected 字段、`proof`、`business_pass`，adapter 却把 `baseline_saved_campaign` 放在外层。修复把来源说明移入内层 `proof`，保留严格身份、同帧和字段集合校验。新增两项回归分别证明旧 handler 被拒绝、修复 handler 通过；采用后 MAIN 的全部 7 项相关测试实际通过。它们不授实机或产品通过信用。

原 host 保留 Popen 的 wait 返回 1；managed cleanup / thread finished 为 true，shutdown tree gone、job active processes 0。native session 原 process exit 保持 NULL，shutdown CK3 exit 为 1，不能写成正常退出 0。keeper 原父进程实际 exit 0、线程退出且无 failure；CAS 4415→4416 于 09:21:34 UTC 释放。ROOT 直接审阅新鲜 Steam 位移截图中的“离线模式”，恢复原 1024×768×32@60 桌面。4 GiB 容量预约于 09:30:30 UTC 关闭，remaining 0。

六个互斥已知根的 logical subtotal 为 705,185,114 bytes，来自已有 source/seed index 与有界 metadata；不等于全项目占用、物理分配或历史峰值。cache 原到期仍为 Oct17 03:03:44 UTC；源码/非缓存 profile 14 天、raw 30 天、小记录 180 天，必要保护有限期且不自动续存。

下一场只需修复后的新 prepare / allocate。实际 runtime 的 `repo_root` 指向 MAIN，case adapter 独立冻结；Source09 index 没有 holder adapter/test。因此共享 Source09、native 和既有 v2 seed 可沿用，无需 Source10、v3、另一个源码导出或新缓存快照。旧 case002/hook 和本场失败均保持原样。

[精简索引](INDEX.json)记录 31 个逻辑条目、30 个压缩对象；归档 41,155 bytes，CRC 和全部对象 SHA 复验通过。归档不重读存档、native report、wire 或大 inventory；原报告 pin 与实际启动输入摘录分别保留。补充记录包含 MAIN 7 项测试、公共命令、容量关闭及分类期限。旧原件继续按通用时效策略管理。[归档验证](VALIDATION.actual.json)。一期仍未 GREEN，正式 I3b/B4、B5、C3、I4 未由本场推进。
