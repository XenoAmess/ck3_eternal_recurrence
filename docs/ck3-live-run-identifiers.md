# CK3 实机验证编号

## 新格式

从 2026-09-12 起，新实机 attempt 使用：

```text
<machine-id>--<mod-key>--R<四位以上序号>
```

示例：`gaming-rig-a1b2c3d4e5--auto-upgrade-buildings--R0007`。

- `machine-id` 标识执行机器。默认由主机名加本机稳定标识的 SHA-256 前 10 位生成，不公开原始 MachineGuid；需要人工管理机器名时可用
  `XAR_CK3_MACHINE_ID` 覆盖。
- `mod-key` 必须来自 `tools/ck3_live_run_id.py` 的 canonical 清单，避免同一产品因拼写变化分裂成多个计数器。
- `R<n>` 只在同一 `machine-id + mod-key` 命名空间内递增。不同机器、不同 mod 都从自己的 `R0001` 开始；不再存在跨项目的全局 R 号。

因此，短写 `R0007` 只允许在已经明确机器和 mod 的局部上下文中使用；正式报告、artifact 根目录、任务总线状态和跨文档引用必须写完整 ID。

## 分配与落盘

分配器入口：

```powershell
py tools/ck3_live_run_id.py machine
py tools/ck3_live_run_id.py list-mods
py tools/ck3_live_run_id.py allocate --mod auto-upgrade-buildings
py tools/ck3_live_run_id.py status --mod auto-upgrade-buildings --run-id <完整ID> --status voided --reason "说明"
```

计数状态位于本机 `%LOCALAPPDATA%\XarCk3Acceptance\live-run-ids-v1\<machine-id>\<mod-key>\`，不提交 Git。每个命名空间有原子更新的
`counter.json`、append-only `allocations.jsonl` 和 append-only `statuses.jsonl`；文件锁防止同机并发分配重复序号。生命周期状态包括
`launch-started`、`completed-green`、`completed-red`、`superseded` 和 `voided`。测试可通过
`XAR_CK3_LIVE_RUN_STATE_ROOT` 使用隔离状态目录，绝不能消耗生产计数器。

runner 必须在静态/preflight 通过后、任何 CK3 启动前分配编号，并立即在 artifact 根目录写
`live-run-identity.json`。即使后续在启动前失败，已分配编号也不回收；报告用 `ck3_launch_attempted` 区分“已登记 attempt”和“实际启动”。
这让编号保持单调且不会因覆盖失败目录而复用。

同一 CK3 PID 的 Python-only 热恢复沿用原编号；失败后的非计划重跑必须分配新编号。一个预先声明的矩阵可以在同一顶层编号下串行启动
多个 cell，并以 `C01/C02/...` 标识各进程；不得在矩阵结束后把临时追加的重跑伪装成原计划 cell。一次兼容性矩阵若同时把多个 mod
作为被验产品，必须为每个 mod 各分配一个编号，并用同一个 `execution_id` 绑定；不能用某个 mod 的编号代替另一 mod 的验收记录。

## 历史编号

旧 `R1…R410` 是本仓库跨机器、跨 mod 共用的全局序列，只作为 `legacy_alias` 保留。历史 artifact 和文档不得重命名或改写；引用旧证据时
同时注明其完整新编号映射。新编号的局部计数不从 410 延续。

“自动升级建筑”本轮在机器 `desktop-3fevhd2-1c74096080` 的迁移映射已经登记：

| 旧 alias | 完整新 ID |
| --- | --- |
| `R405` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0001` |
| `R406` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0002` |
| `R407` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0003` |
| `R408` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0004` |
| `R409` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0005` |
| `R410` | `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0006` |

后续该机该 mod 的 attempt 从 `R0007` 开始。迁移过程中由 mock 单测错误消耗的
`desktop-3fevhd2-1c74096080--zhongguo-style--R0001…R0003` 已在 append-only 状态日志中标为 `voided`；没有删除或复用这些号码。
