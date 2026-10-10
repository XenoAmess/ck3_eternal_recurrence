# 2026-10-11 R53 原生完成绑定拒绝与实际闭场

R53 的公共 `run` 和 `verify` 均实际 exit 2，业务未通过。一期仍为 **75% / NOT_GREEN**；既有冷却消失、全新 365 日循环、B4/B5/C3 和完整 I4 均未增加通过信用。[实际原件索引](acceptance/2026-10-11-i4-natural-r53/INDEX.actual.json)保留 20 份小型原件，共 85,185 B；大存档、截图、完整 native report 和逐文件清理 ledger 留在外置目录并按期限复核。

本场使用 Source11/O11、cbr2、CK3 1.20.0.4、CASE4、a15，冻结 MAIN `3574e41f8b9131ed6a397f21154c1803c13685f3`。新不可变 shader seed 的 3,740 个文件精确注入隔离 profile 与 allocator 输入副本，没有新 source export 或 native build。[公共就绪回执](acceptance/2026-10-11-i4-natural-r53/readiness-window-result.actual.json)实际在原 900 秒内观察到 qualified restore 和 hold，耗时 **314.4712155 秒**。本场比 R52 更早进入业务，但没有直接测量缓存命中，不能将全部启动差异归因于缓存。

## 业务停止原因

初始决议不可用，新 SAVE 回读证明冷却 flag 仍在；该 SAVE 正文读一次，没有重读原 baseline。随后实际完成 **28 个自然日、672 小时**的逐日推进。初始观察加前 27 天的 28 次完整观察通过，最后一次 confirm 仍为 false。第 28 天的前置模型返回 `available=false`、`frame_verified=false`、`unavailable_reason=pipe_completion_keyed_query_binding_changed`，adapter 正确停止。没有选派动作、最终到期 SAVE 或失败查询重放。

[选定字段与诊断](acceptance/2026-10-11-i4-natural-r53/observation28-diagnostic.original.md)确认请求/详情 key、PID15488、连接世代1、玩家31254、日期以及 GUI owner/actor 资格仍匹配；后继详情树可读。原生 completed-mailbox 分支的判断是 `!ReadSnapshot(completion) || completion != current || state_revision != expected_revision`。原 DTO 没有记录这三个谓词的独立结果或两个内部 Snapshot，**确切失败谓词/字段仍 UNKNOWN**；后来的同身份帧不能推翻中间拒绝。command `ok:true` 不能覆盖模型不可用。

后继[每日帧复用](2026-10-11-i4-day-frame-reuse.md)已单独测试并采用，只减少一次日常公共提交，不宣称修复这个原生拒绝。下一共享源码工作先补失败谓词和有界 Snapshot 差异诊断，保持原守卫、不重试，不直接重复整场。首版诊断草稿经独立审阅发现新增分配异常可能改变 `noexcept` worker 的失败行为，尚未采用；后继必须先保持原拒绝结果，再使新增诊断为 best effort，并完成必要检查。

每日帧复用提交 `cdcd276ddcdce89b7dffe21ab5399f3d0e2e2591` 的[官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38077717974)与[线性历史检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38077717985)均已实际终态 success；这不增加 R53 业务通过信用。

## 实际闭场

以下均为 2026-10-11 CST 的原实际时间：

| 事件 | 时间 |
| --- | --- |
| qualified restore 完成 | 02:02:45.236511 |
| 第 28 天模型步骤记录完成 | 02:21:02.318917 |
| CK3 正常退出与 native 会话结束 | 02:36:53.870223 |
| 原 host 完成 | 02:37:00.694782 |
| 原 host Popen wait 0 | 02:37:01.157891 |
| keeper 原线程结束、allocator 原等待 0 | 02:39:50 |
| CAS release，task done/resources=[] | 02:40:12.328468 |

Root 直接审阅原始桌面图，核窗口与控件焦点及英文布局，经统一坐标换算操作中文退出菜单、取消 `autosave_exit` 后正常退出到桌面。[正常闭场原件](acceptance/2026-10-11-i4-natural-r53/normal-close-result.actual.json)包含实际保留句柄 OS exit 0、native exit 0、job/tree/control 清理、host finish-hold 与线程结束；keeper 最后 owned sequence4586，CAS 释放后4587。桌面恢复原 **1024×768**。本场保持 Steam 离线，没有在线切换。生命周期 GREEN 与公共业务 RED 分开记录。

预约004在 02:56:30 前完成实际闭账：未来写入预约剩余0，限定明确范围保留逻辑量 **1,056,211,427 B**，当时 C 盘可用 **621,170,180,096 B**。未枚举小增量实际值为 null、保守上界32MiB，不混入已测小计；物理分配量及历史峰值仍未知。[闭账回执](acceptance/2026-10-11-i4-natural-r53/reservation004-closed.actual.json)没有续长 Oct17 缓存期限或 Oct12 配额期限。

## 并行重复缓存回收

R52 已完整闭场，其原可变缓存的当前用途已被同字节不可变 seed 和 CASE4 输入替代。Root 明确收缩该精确重复副本的保护，经逐项文件身份、占用、保留源/目标句柄 SHA 和删除后缺失读回，四批实际删除 **3,740 文件、146,942,031 B 逻辑量**。API 分配量之和为155,353,904 B；各次卷空闲变化有并发影响，不全部计作清理释放量。最终目标内剩余文件0，空目录保留。

前两次 batch0 请求因 ROOT/coordinator 租约不新鲜而在领取删除批次前拒绝，没有删除；原拒绝保留。此后四批全部成功，没有逐项失败、自动重试或递归删树。不可变 seed、R53 缓存和原失败证据保留，原 R52 READINESS_RED 不变。[最终可用性回执](acceptance/2026-10-11-i4-natural-r53/cache-retirement-final.actual.json)明确标记旧 R52 mutable payload 已删除；旧 manifest 路径只代表历史身份，不代表原件仍可读取。大 ledger 最晚2026-11-09复核，精简记录180天复核；复制、哈希及本次收口均不续期。
