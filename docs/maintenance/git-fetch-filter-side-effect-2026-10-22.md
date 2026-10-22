# 2026-10-22：Git fetch 过滤配置的持久副作用

机器 `desktop-3fevhd2-1c74096080`。本记录区分一次已执行命令、当前配置、后续未知执行者的后台 fetch，以及正常的单键修正，不以来源推测冒充完整因果证明。

2026-10-22 03:44 UTC，为合回已经审阅的一文件测试修复，发布控制器执行过一次精确提交 fetch，带 `--filter=blob:limit=1048576`、明确祖先 negotiation tip、`--no-tags`、`--no-write-fetch-head` 和禁自动维护。原 PID 24436、创建时标 `134371142455809011`、原 wait0 见[原回执](evidence/git-fetch-filter-side-effect-2026-10-22/FETCH-ORIGINAL-WAIT.actual.json)。这次控制器保存的新 pack 文件集合增量为 0；后续本地提交完成，非强推因远端并发提交被拒，原失败未删除或改成成功。

但该显式 filter 不只是一次传输参数：`.git/config` 的实际 mtime 为 03:44:05.632942 UTC，后读 `remote.origin.partialclonefilter=blob:limit=1048576`。该值与本命令一致，应如实记为我方命令的持久配置副作用。**执行前没有保存该 key 的原快照，原值为 unknown**；不能据常见默认值猜成 `blob:none`，也不能称后来修正“恢复了原值”。

04:47:50 UTC 实际只读配置为 12152 B，SHA-256 `4fdc1a96dccffbde0eedf348e6c16d6d5fb45f4d16c3cfc4fa9100ec01c2f48f`：
`remote.origin.promisor=true`，filter 为上述 limit 值，`extensions.partialClone` 不存在，无 config.lock，当刻未观察到本仓库 Git/fetch 进程。这个瞬时检查不能排除周期后台活动。后续 reflog 中有 `fetch origin --prune` 活动及较大 pack 增长，执行者仍未核实；不能把所有卷增长直接算给 03:44 的精确提交命令，也不能把未知执行者说成已经找到。

Root 独立授权后，04:52:00.839017–04:52:02.803374 UTC 运行一次正常仓库本地命令：

```text
git -C D:/workspace/ck3_eternal_recurrence config --local --replace-all remote.origin.partialclonefilter blob:none
```

原 PID 35804、创建时标 `134371183226264645`、原 wait0。后读配置为 12143 B、SHA-256 `d1f458d8867e7d02b2bbd1f0115ac82f7d67c3085cf5700d4b0432188f998931`；逐字比较仅该值减少 9 字节，promisor=true、extension 缺失及全部其他字节保持。三 key 前后读取原退出码分别为 0/0/1；exit1 在这里明确表示该 extension key 缺失，不改记为命令失败。见[修正原件](evidence/git-fetch-filter-side-effect-2026-10-22/FILTER-CORRECTION.actual.json)和[独立容量闭场](evidence/git-fetch-filter-side-effect-2026-10-22/FILTER-CAPACITY-INDEPENDENT-CLOSED.actual.json)。

这是共享该 `.git` 的 worktree 后续默认 origin 过滤策略修正，没有 fetch、索引写入、pack 删除、GC、repack 或 prune，也没有回收已有空间。显式参数仍可能再覆盖它，必要的按需 blob 获取也不是被永久禁止；未来重型操作仍需实际预算。完整旧 config 仅以本地小 gzip 备份保存，不把含机器专用设置的整个 config 作为公开来源包导出。

后续取对象前先保存实际 filter/promisor 值及 config 字节数、SHA、mtime，明确是否要改变持久策略；不能假定一次命令的 filter 对其他 worktree 无影响。本轮的另一条容量勘误见[同一写入不能同时算 ownP 和额外等额物理要求](storage-reservation-self-double-count-2026-10-22.md)：同一次 peak、其他未消费 future、系统增长与 floor 各计一次，不能制造重复预留导致的假缺口。该勘误不授权手删 `.git` 或把全部卷剩余变化贷记给某一回收批。
