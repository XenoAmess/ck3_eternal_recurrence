# R220 / R0216：host 失败且正常闭场原件缺失时的资源接续

`machine_id: desktop-3fevhd2-1c74096080`。2026-10-20T03:20:10Z 实读 R0216 原 host wait=1、public wait=2，native report 为 RED；原报告保存 Job/tree、控制文件和空进程清理证据。keeper 原 parent wait=0、`thread_exited=true`、最后序号 7189，实际 CAS **7189→7193** 为 done、resources 空。证据均精确绑定本场 frozen/READY/prepared、原角色运行上下文与文件 SHA；这些机器状态不能外推到其他机器或下次现场。

`case-output/normal-close-result.json` 和 `actual-retained-handle-os-exit.json` **实际不存在**。原件仅有 `normal-close-error-preserved.json`，其错误与 `entry-run-result.json` 相同。不能补造缺失文件，也不能把 native report 中的 CK3 exit=1 写成原 retained-handle 回执。

[共享 allocator](../../tools/ck3_mod_acceptance_allocate.py) 在既有 failed-live schema 中新增 `closure_kind=failed-host-without-normal-close-result`。它要求原 host 非零 wait、native RED 且完整 Job 清理、public 2、allocator 0、源绑定的 case/normal-close error、原 retained 身份、真实 keeper report/parent 0、精确 closed CAS，以及当次原进程、runtime/controller、所属 recorder 和控制文件已缺席。已有 normal/OS 原件、未匹配的失败类别或缺失必要证据仍拒绝。原 failed-live 严格路径和 R219 expired-missing-report 路径均保持原条件；此分支仍通过外层真实 `closed_lease` 检查。

结果仅为 `previous-shared-failed-host-missing-normal-resource-closed`。`normal_close_result`、`retained_os_exit_receipt`、`original_ck3_exit_code`、`native_cleanup_qualified` 保持 null；`native_reported_ck3_exit_code=1` 单独标明来源。正常闭场、typed exit、retained OS0、业务和发布资格均 false。

- [当前 native 报告精确投影](evidence/episode04-r220-missing-normal-predecessor-20261020/native-cleanup-projection.json)：首次单次读取并哈希本场 15,704,288 B 原件，SHA `1dc5c4cc30615a82ebcf95a00c05e700ec57694f7516ef009bb19394d97bcc81`；后续沿用已有小 projection 协议，仅核原报告路径／大小和原 host wait，不重复读取大报告。
- [真实资源验证](evidence/episode04-r220-missing-normal-predecessor-20261020/actual-validation.json)、[失败闭合输入](evidence/episode04-r220-missing-normal-predecessor-20261020/failed-live-resource-closure.json)、[下次公共 allocate 参数](evidence/episode04-r220-missing-normal-predecessor-20261020/actual-inputs.json)：仍使用四个既有 `--previous-*` 参数，前驱为 R0216。
- [focused tests](evidence/episode04-r220-missing-normal-predecessor-20261020/focused-tests.json)：35/35，含新增 12、R219 13、既有 failed-resource 10。覆盖未匹配失败、假正常／零退出、残留进程／recorder／controls、错误来源／公开命令／keeper／CAS及真实缺失原件。
- [精确应用回执](evidence/episode04-r220-missing-normal-predecessor-20261020/integration.json)：已验候选逐字节应用于 `76dcbf7fe4526117fc25f0c892593b570f0a8b68` 基线；native tree 未改。实际下一场仍须新鲜准入，不把本页当启动或业务资格。

外置小输入保护至下一场分配后复核，最迟 2026-10-27T03:20:10Z 按通用存储策略复核。本包未启动／结束游戏或录制，未操作屏幕，未删除资产。
