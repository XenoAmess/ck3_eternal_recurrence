# Exact HEAD 8c0ddff7c 官方 CI 终态

HEAD **8c0ddff7c477311e18f0a4517566df412e5f49c9**；parent `ca3888b11393df33425789532b3b6604d658ff55`。本包只读此 exact HEAD 自动 push 的真实 run/job/check API，初始 Official pending 原件保留，实际终态如下。

| Workflow | 实际结论 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | SUCCESS | [37729515030](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515030) / [113155217275](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515030/job/113155217275) | 2026-10-08T04:51:48Z → 2026-10-08T05:00:34Z |
| Linear history | SUCCESS | [37729515003](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515003) / [113155217680](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37729515003/job/113155217680) | 2026-10-08T04:51:48Z → 2026-10-08T04:52:22Z |
| Li Yu Dao static checks | NOT_TRIGGERED / NULL | NULL | NULL |

两个已触发 workflow 的 final check 亦为 SUCCESS，job API 的失败步骤为空。没有把父 4c CI 成功或本地 source/native checks 代替本次 8c 结论。

Li Yu **NOT_TRIGGERED / NULL**，不是 GREEN。官方 PushEvent `23338298265`（push_id `45809275882`、UTC `2026-10-08T04:51:44Z`）明确 before `ca3888b11393df33425789532b3b6604d658ff55` / head `8c0ddff7c477311e18f0a4517566df412e5f49c9`；官方 compare 一提交、20路径、ahead1/behind0。所有路径均不匹配 exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6` 的四项 push filter，final exact run list 没有 Li Yu run。完整来源及 path 清单见 `TRIGGER-PATHS.source-facts.json`，没有以 tip parent 猜 event before。

本次 12 次只读官方 API GET，读取失败 1 次。`runs-002` 的 WinError10061 连接拒绝原件保留，随后同 exact API 成功；传输错误不当 CI RED。按 ROOT 本轮限定范围，**完整 job log / producer stdout 均 NULL，下载尝试0**；只保留必要 run/job/check/step 结构化原件和一次 Linear annotation API，不重做旧 4c 多轮日志/auth 尝试。此前缺失日志与旧失败均保持历史。

所有 raw API response、错误、读取回执与 SHA 在 `INDEX.json` 和 `raw-official-evidence.zip`，一次 ZIP 字节校验见 `ARCHIVE-CHECK.actual.json`。没有 MAIN/Git/SDK/CK3/进程/屏幕/总线/设置、本地测试/构建、workflow rerun 或 dispatch。CI 不授予新 DLL/live/正式业务/newT/C3/I4/退出 GREEN；whole mod **NOT_GREEN**。
