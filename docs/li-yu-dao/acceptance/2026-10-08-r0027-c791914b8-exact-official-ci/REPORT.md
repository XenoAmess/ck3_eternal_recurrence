# Exact HEAD c791914b8 官方 CI 终态

目标 **c791914b84b9eb7cf0a83b94d55c25fb24175157**；parent `574c015bd7e6e37eb6cbb3f5b88bdd868b1a4bab`。官方 GitHub REST精确 `head_sha` 返回当前自动 push 的 3 个实际run。

| Workflow | 实际终态 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | completed / failure | [37704098208](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098208) / [113074230660](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098208/job/113074230660) | 2026-10-07T23:46:05Z → 2026-10-07T23:50:14Z |
| Linear history | completed / success | [37704098241](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098241) / [113074230426](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098241/job/113074230426) | 2026-10-07T23:46:01Z → 2026-10-07T23:46:51Z |
| Li Yu Dao static checks | completed / success | [37704098239](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098239) / [113074230607](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37704098239/job/113074230607) | 2026-10-07T23:46:01Z → 2026-10-07T23:46:51Z |


**Official Runner CI** 的实际 failed step：31「Test Reclaim the Motherland release tooling」。原错误为 2026-10-07T23:50:10.8837870Z AssertionError: 3 != 2。最小原因：Reclaim the Motherland contract assertion; no RMTM changed path in this commit。原 producer log、traceback 与 file/line均保全，未运行本地测试或修改源。

Li Yu 本次实际触发：exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6` 的过滤与本提交 17 个paths中 1 个mod路径相符，所有paths及原workflow保存于 `FINAL.actual.json` 和原API。CLA的server bypass提示不是CI结论；没有沿用574/198/720的旧结果。首次 actual API 读取时三个 run 已全部 terminal，没有观察到 pending，也没有制造等待记录。三个 job 各一次完整原日志下载与 exit0回执均保存，stdout不是截取投影；旧574 LiYu RED保持历史原样。

本轮 9 次只读官方REST GET调用，read error 0 次。完整当前API/jobs/failed producer stdio以bytes/SHA收录 `INDEX.json` / `raw-evidence.zip`，必要解包核验记录在 `ARCHIVE-CHECK.source-facts.json`。CI只证明本exact source的实际检查结果，不能替代新DLL/live/正式批准/newT/C3/I4/typedexit验收；whole mod **NOT_GREEN**。

没有MAIN/Git/SDK/游戏/进程/Steam/屏幕/总线动作，没有dispatch/rerun、本地旧CI或测试重跑，也未修foreign RMTM代码。
