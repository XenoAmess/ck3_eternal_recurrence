# 运行验收器写入错误上下文：2026-10-06

接续[10 月 6 日交接](../ck3-upgrade-handoff-2026-10-06.md)的 H81 候选，将最小诊断改动应用到正式[运行验收器](../../ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py)。它为实际 `OSError` 记录写入目标和子操作，并重抛同一异常。此项不解决磁盘压力，也未取得新 CK3 实机或经商贪腐业务通过。

## 原故障与改动范围

CCC R4 最后成功步骤为 `a77-tier4-advance-D3-once`，UTC `09:05:52.545882` 完成，随后没有追加下一 D3 frame；UTC `09:05:55.565978` 出现 `Errno 28`。旧记录没有原始 traceback 或 filename。[原诊断](../handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-r4-write-diagnostic-candidate.json)只支持 `execute finally → self.write → run.write → write_atomic_report` 的控制流推断；原场具体失败子操作和瞬时容量成因仍为 UNKNOWN，原 RED 保留。

本次只应用[5404 B 小 patch](../handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-write-error-context-NOT-APPLIED.patch)对应的诊断逻辑：

- `JsonLines.write` 标注 append 文件的 open、write、close，以及 journal direction。异常路径释放原锁后重抛。
- `write_atomic_report` 标注 UUID partial 的 open、write、flush、fsync、close，或从 partial replace 正式 report；保存两个路径、phase、最后步骤 ID、ok 与 finished_at。
- `annotate_write_error` 将原异常类型、消息、errno、winerror、filename/filename2 与 traceback 附在同一异常属性和 `add_note` 上，不增加文件写入。
- `run` 的既有异常收集点保存 traceback 和已存在的 write context；outer catch 用 `setdefault` 保留较早上下文。

原 atomic 的 20 次 Windows `PermissionError` 重试及 `0.05s` 间隔保持。ENOSPC 不新增 retry、吞错或业务续跑。`PlanClient.execute`、预算、产品脚本、DLL、Source10、旧 H81 与已消费场的冻结输入未改。

覆盖范围是上述两个 writer，并非所有文件 I/O。初始目录创建、配置快照和 server stderr 等其他路径不在本次诊断覆盖内。持续空间不足仍可能令既有收尾 report 写入失败；附在异常上的信息不承诺最终 JSON 一定成功落盘。下一执行者需继续保全既有 stderr、完整 report 和 partial。

## 验证与复用边界

[本次 byte/AST 回执](runtime-write-error-context-2026-10-06-evidence.json)记录正式源码为 102471 B / SHA-256 `b75cc3a6eb7cea83c00fadf4316bdf6c798e38541e6d4fc88735f436bc67d2a3`，修改前为 100207 B / `e47fd1bad5efaf0f2dd1f8993197aae2359ce70c69ca89442c1d392af8e92c32`。小 patch 在内存中精确重建完整 H81 候选；四份有关归档逐字节符合索引 SHA，且等于外置原件。语法编译、diff whitespace 和实现定义范围检查通过。

正式源码的 `JsonLines`、`JsonLines.write`、`annotate_write_error`、`write_atomic_report` AST 与已审候选完全相同，因此复用[九项既有回执](../handover/2026-10-06-ck3-upgrade-handoff-artifacts/ccc-nine-writefaults-receipt.json)中的前八项 writer 注入信用，不重复其测试。该九项回执仍绑定原候选 SHA `568d9aeecf7b2a4d758017de138349de04f7b2dad29b76fa29cf8157dcc5df33`，不改成新源码结果。

master 与 H81 的 `PlanClient.execute` 等定义有差异，第九项“完成 advance 后 finally writer 失败”的原信用只属于 H81。本次在正式模块增加一个针对当前实现的检查：第一次 report 成功替换，advance 与 after snapshot 完成后第二次 fsync 注入 ENOSPC；验证同一异常逃逸、最后步骤保留 ok/finished_at、后续步骤未派发、上个完整 report 与失败 partial 都保全。

从 `ck3_autonomous_player/native_bridge/research/` 运行：

```text
C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe -m unittest test_ck3_12002_mcp_live.AtomicReportWriteTests -v
```

现有 atomic 成功、写入失败、Windows 瞬时和永久拒绝，加上新增当前 execute 检查，共 **5 tests PASS，0.196s**。首次从仓库根按 package 名导入因 helper 的顶层 import 找不到模块而失败，未执行测试；回执保留该次调用，正确 cwd 后取得上述结果。没有重跑整套矩阵，没有游戏、SDK、native bridge 调用或真实磁盘耗尽试验。

## 下一场冻结

完成本包 master 提交后，冻结新工作目录、source commit、harness 文件大小/SHA、解释器、实际 Source10 consumer 和新 profile/run 的绑定。旧 R4、inputs-08、Source10 producer/consumer 及归档字节继续原样保留；新场仍需新分配、nonce、离线画面与唯一操作者。

完整旧候选包含 H81 已备业务/readiness overlay，115287 B / SHA `568d9aeecf7b2a4d758017de138349de04f7b2dad29b76fa29cf8157dcc5df33`；它与新正式源码并不相同。CCC 下一场如沿用这个完整候选，必须明确登记为“原 H81 + 本次 diagnostic overlay”，绑定其精确字节和既有有限证据；不能将完整候选覆盖正式源码，不能声称其所有 overlay 已合回 master。诊断已入正式源码也不能反向更改旧场的运行输入或评价。

状态：源码集成及有限离线验证通过；本子任务不执行 commit/push，由 root 统一立即交付。新冷场、容量问题解决、CCC 剩余生产 UI 与正常 GUI 退出仍待实际执行。
