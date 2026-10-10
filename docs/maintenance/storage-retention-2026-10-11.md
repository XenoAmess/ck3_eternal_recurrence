# 2026-10-11 LYD 容量与到期复核

执行统一 [存储保留策略](../storage-retention-policy.md) 1.0.0。00:11 CST，Root 在既有卷独占锁内重新核验任务总线、进程、实际可用空间及原配额，创建独立预约 003；前一预约 002 已实际 CLOSED/0，没有并存的旧未用峰值预约。

| 项目 | bytes |
| --- | ---: |
| 上一保守已有使用量 | 131233343898 |
| R51 已观测新增保留逻辑量 | 838105040 |
| 本轮小源码与审计预计入 | 134217728 |
| 本轮保守已有使用量 | 132205666666 |
| 新峰值预约 | 4294967296 |
| 已有量加新峰值 | 136500633962 |
| 原配额 | 137438953472 |
| 计入后配额余量 | 938319510 |
| 准入时 C 盘可用 | 622757015552 |

本轮预算含 Source11 导出上限 192 MiB、native build 0、新缓存 seed 快照/复制 0。仅允许已有缓存与当前精确 key 一致时使用，否则冷启动；不放宽 key。存档输入与必要输出仍计入 4 GiB 总峰值。

预约实际截止为 `2026-10-10T22:11:10.391492Z`，原配额截止 `2026-10-12T05:19:51.814083Z` 不变。Source11 继承 Source10 的 `2026-10-17T08:45:50.800231Z` 复核时间；缓存/profile 原复核时间保持。这里记录有限保留，不将复制、访问、续跑或入库视为续期。

本轮对已有分类、复核集合的结论为 **NO_ELIGIBLE_CANDIDATE**。先前重复 payload 已退役，当前 v2 缓存、B3/D2a、Source09/O10 与未解代表失败仍有用途且未到原期限；没有新增删除，没有重复全树扫描，也没有将过去的删除量再次累计。此结论只覆盖已有已复核集合，不能外推全盘没有过期文件。

[原始准入与协调回执](../li-yu-dao/acceptance/2026-10-11-i4-source11-preflight/INDEX.actual.json) 已保留。当前预约仍开放；实际场次结束后须核验独立进程退出、keeper/CAS 及限定新增资产元数据，再将未来写入预约归零。释放 4 GiB 预约不是物理删除 4 GiB；实际保留量、全项目占用、历史峰值分别报告。

01:00 CST 追加实际闭账：R52 公共 readiness RED 保留；正常 GUI 行政退出取得实际 OS0/native0/原 host wait0，keeper 线程及 allocator 原等待0，最后 owned4551 已完成 CAS release、done/resources=[]。预约 003 于 00:59:18 实际 CLOSED，剩余未来写入预约 **0 B**；限定新增目录的保留逻辑量 **441327935 B**，闭账时可用 **622230110208 B**。[原闭账](../li-yu-dao/acceptance/2026-10-11-i4-natural-r52/reservation-closed.actual.json)与[限定元数据测量](../li-yu-dao/acceptance/2026-10-11-i4-natural-r52/reservation-measure.actual.json)仅覆盖新 CASE3/run/a14/Source11/O11 及指定小回执，不代表项目全量占用或历史峰值。后写的闭账与发布文件不在该次测量小计内；并行小源码仍由原 128 MiB 预计入覆盖。

缓存/profile 原截止、Source11/O11 继承复核上限与原配额 2026-10-12T05:19:51.814083Z 均未延长。有限新证据按原策略登记复核；本轮实际物理删除 **0 B**，不把 4 GiB 预约释放或过去的清理再次累计。自动预约/自动 GC 尚未实现。


## 2026-10-11 03:03:23 CST：R53 原生完成绑定拒绝、正常闭场与重复缓存回收

[实际闭场与清理记录](../li-yu-dao/2026-10-11-i4-r53-native-binding-refusal.md)及[最终可用性回执](../li-yu-dao/acceptance/2026-10-11-i4-natural-r53/cache-retirement-final.actual.json)：只删除已闭场R52原shadercache的3740个同字节重复文件，逻辑量146942031B，API分配量之和155353904B。每批≤1000，原件与保留seed均以实际持有句柄核SHA后删除，最终原manifest路径全部缺失且目标剩余文件0；未递归删除目录。旧mutable payload现在不可读，保留immutable seed及R53输入，不改写R52业务RED。两个preclaim新鲜租约拒绝原样保留，四个实际批次均成功。当前seed仍按原Oct17期限复核，大ledger最晚Nov9复核、精简回执180天复核，没有自动续期。

预约004已在原卷协调锁内按实际host/keeper等待和CAS释放闭账，未来写入预约剩余0。限定CASE4/R53/a15、新seed与指定小回执范围保留逻辑量1056211427B；额外未枚举小增量actual=null，保守上界32MiB，不冒充整个项目总占用。物理分配量与历史峰值未知，闭账时卷空闲621170180096B；并发空闲变化不全部归因于清理。Source11/O11/native/原campaign seed未重计；缓存Oct17及配额Oct12原期限未续。通用策略仍1.0.0，其他机器未运行的清理没有被标为已执行。

03:22 CST，[focused预约005](../li-yu-dao/acceptance/2026-10-11-i4-native-completion-diagnostics/storage-closed005.actual.json)实际闭账。峰值预约128MiB仅供3TU定向编译、EXE和回执，无source export或完整DLL复制；限定build和3个命令目录保留逻辑量17421872B、1792项metadata，未来预约0、物理清理0。基数沿用004保守占用+实际保留+32MiB未知小增量上界，没有抵扣缓存删除；原缓存和配额期限不续。新build按策略Oct24复核。编译及测试通过，Defender设置失败独立保留；自动预约/GC仍未实现。
