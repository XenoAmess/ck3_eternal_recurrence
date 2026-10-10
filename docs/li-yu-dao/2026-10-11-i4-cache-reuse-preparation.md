# I4 CASE4 复用 R52 缓存的实际准备

截至 01:43 CST，公共 `prepare / plan / preflight` 均实际 exit 0，`blockers=[]`。CASE4 已准备 R52 缓存的隔离副本；尚未 allocate/启动，业务状态仍 NOT_ASSESSED。一期保持 **75% / NOT_GREEN**。

此前 R51/R52 虽开启共享缓存许可，但没有选择 seed，见[追查](2026-10-11-i4-r52-readiness-timeout.md#缓存选择追查本场之后)。本轮仅核 R52 精确 shadercache 根，实际有 **3740 文件、146942031 B**，未进行全盘或旧证据树扫描。公共 v2 冻结函数完成八份来源、启动前业务快照、完整 runtime/profile key、原生闭场及 keeper/CAS 核验，实际快照完成于 01:31:42；随后只在新输入顶层追加该 seed 的实际 manifest pin。

公共 prepare 实际通过 source/current key 一致性检查，并复制到新隔离 profile；preflight 再核精确输入。复用已有 **Source11/O11 与 cbr2**，新增 source 导出和 native 构建均为 **0**。新案例绑定已推送的[两查询批量提交](2026-10-11-i4-batched-observation.md)，原 900/8400/7200 秒预算、逐日事件检查和 366 日上限保持。缓存键匹配及副本一致不证明游戏实际命中缓存，也不授启动速度、自然到期、B4/B5/C3 或完整 I4 信用。

[小型实际证据](acceptance/2026-10-11-i4-cache-reuse-preparation/INDEX.actual.json)保留准入、缓存来源、快照、实际输入绑定及公共命令回执。preflight 原 stdout 为 2051904 B，外置原件保留精确 pin，Git 仅接收 5239 B 有界投影；大清单、缓存、游戏和存档正文不再复制进仓库。

预约004在原卷协调锁内实际核总线、进程和 free 后准入。保守已有量 **132781212329 B**，加本轮总峰值 **4294967296 B** 后为 **137076179625 B**，未超原 **137438953472 B** 配额；缓存快照和两份可能的运行副本各按 192 MiB 计入同一总峰值，没有为缓存另领配额。预约截止 `2026-10-10T23:30:27Z`；原配额截止 `2026-10-12T05:19:51.814083Z`、缓存复核 `2026-10-17T13:06:29.278808Z` 均未续期。预约仍开放，实际闭场后按限定新增量闭账，不能把释放预约算成物理删除。

本轮既有已审清理集合无新增可删项，实际删除 **0 B**；这不外推全盘没有过期资产。后续若出现已核验替代的冗余副本，再按统一策略逐文件回收。统一自动 GC/预约器仍未实现。

B5 [并行字段研究的小型实际证据](acceptance/2026-10-11-b5-saved-title-fields/INDEX.actual.json)记录：实际完成一次 R26 原存档流读与完整 SHA 核验，仅提取目标宗教 Title18373 的 719 B 原始行并生成 4446 B 小型结果，五项 selector 检查通过。实际行包含 `definite_form`、`destroy_if_invalid_heir`、`no_automatic_claims`、`always_follows_primary_heir` 四个 `yes`，以及法律 bare list 的 `temporal_head_of_faith_succession_law`。该 R26 是保护检查失败世界，只用于字段研究，不能成为 B4/B5 的有效基线；原生字段别名和保存语义证据仍在施工，B5 adapter 尚未采用。
