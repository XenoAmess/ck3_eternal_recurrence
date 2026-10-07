# R0019 exact HEAD push CI：实际最终结果

精确来源为 `465595b67efa8f72dfc97bc0de218302c75e3bfd`，repository `XenoAmess/ck3_eternal_recurrence`。只记录此 HEAD 自然触发的 push，旧 3475 GREEN 或 dbaf 结果均不外推。

| Workflow | Actual run / ref | Final result |
| --- | --- | --- |
| Official Runner CI | [37566880803](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37566880803)，attempt `1`；`push/refs/heads/master`，exact HEAD 如上 | `completed/success`，GitHub updated_at `2026-10-07T03:36:46Z` |
| Li Yu Dao static checks | exact HEAD 无实际 run；GitHub commit 的实际 changed-files 没有命中既有 workflow paths | **NOT_TRIGGERED，不能记 GREEN** |

Official Runner 的实际 final API 和 jobs 已保存；此回读没有发现该 run 的失败 step，因此不额外下载整份成功日志。原最终 receipt 与 job IDs 见 [FINAL.actual.json](FINAL.actual.json)，原 API stdout/receipt 原字节及 SHA 见 [INVENTORY.json](INVENTORY.json) 和 [CI.original-evidence.zip](CI.original-evidence.zip)。Li Yu Dao 的路径过滤原文与 exact commit 的原 API/changed-files 也保全。

第三次只读 gh GET 在本机编译负载期间实际达到 180 秒 timeout，stdout/stderr 均为空，exit code 为 null；该读取的原 receipt 和 FAILED.transport JSON 原样保全。它是 **传输失败**，不是 CI RED；后续新只读调用成功取得此实际最终结果，没有 dispatch/rerun，也没有修改任何历史 attempt。

本报告提供 **CI 信用**。它不授予此 HEAD 的 native compile、CK3 live、formal、新 T、C3 或 I4 信用；这些结果只按独立 actual 编译与新 cold-run 证据判定。主执行树的运行输入从此 HEAD 冻结，文档后续追加不改变该 frozen 来源。

外置原 attempt 为 `C:/workspace/ck3_lyd_runtime_20261004/r19-exact-ci-20261007-001`。本包 create-only 写入独立 `C:/lci18w1`；主树写入、旧 tests、native compile、SDK、游戏、bus、CI rerun/dispatch、commit/push 均为零。
