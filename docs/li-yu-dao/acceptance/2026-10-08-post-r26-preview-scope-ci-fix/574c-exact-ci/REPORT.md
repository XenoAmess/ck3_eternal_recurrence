# Exact HEAD 574c015bd 官方 CI 终态

目标 **574c015bd7e6e37eb6cbb3f5b88bdd868b1a4bab**；parent `1982837ee25a9991c8bfdf9285913d2d84d44236`。官方 GitHub REST精确 `head_sha` 返回当前自动 push 的 3 个实际run。

| Workflow | 实际终态 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | completed / failure | [37702997764](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997764) / [113070638653](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997764/job/113070638653) | 2026-10-07T23:34:03Z → 2026-10-07T23:38:35Z |
| Linear history | completed / success | [37702997739](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997739) / [113070638184](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997739/job/113070638184) | 2026-10-07T23:34:02Z → 2026-10-07T23:34:42Z |
| Li Yu Dao static checks | completed / failure | [37702997797](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997797) / [113070638610](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37702997797/job/113070638610) | 2026-10-07T23:34:02Z → 2026-10-07T23:34:53Z |


**Official Runner CI** 的实际 failed step：31「Test Reclaim the Motherland release tooling」。原错误为 2026-10-07T23:38:31.3810756Z AssertionError: 3 != 2。最小原因：Reclaim the Motherland contract assertion; no RMTM changed path in this commit。原 producer log、traceback 与 file/line均保全，未运行本地测试或修改源。
**Li Yu Dao static checks** 的实际 failed step：5「Check product and builder」。原错误为 2026-10-07T23:34:49.7571387Z AssertionError: existing script expressions changed: common/scripted_triggers/lyd_i3b_institution_triggers.txt。最小原因：Preview-scope baseline AST checksum assertion for common/scripted_triggers/lyd_i3b_institution_triggers.txt。原 producer log、traceback 与 file/line均保全，未运行本地测试或修改源。

Li Yu 本次实际触发：exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6` 的过滤与本提交 54 个paths中 19 个mod路径相符，所有paths及原workflow保存于 `FINAL.actual.json` 和原API。CLA的server bypass提示不是CI结论；没有沿用198/720的旧结果，初始pending与每次真实状态回执保持。

本轮 10 次只读官方REST GET调用，read error 0 次。完整当前API/jobs/failed producer stdio以bytes/SHA收录 `INDEX.json` / `raw-evidence.zip`，必要解包核验记录在 `ARCHIVE-CHECK.source-facts.json`。CI只证明本exact source的实际检查结果，不能替代新DLL/live/正式批准/newT/C3/I4/typedexit验收；whole mod **NOT_GREEN**。

没有MAIN/Git/SDK/游戏/进程/Steam/屏幕/总线动作，没有dispatch/rerun、本地旧CI或测试重跑，也未修foreign RMTM代码。
