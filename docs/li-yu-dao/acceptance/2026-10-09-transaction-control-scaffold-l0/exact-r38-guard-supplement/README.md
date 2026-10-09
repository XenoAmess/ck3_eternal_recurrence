# R38门禁故障回归补充（2026-10-09）

回归负例同时将终点显示门禁和选项门禁改为相同的错误 holder 条件，精确覆盖R38的故障形态。两门禁相等仍不能使它通过；独立的未授封语义检查明确拒绝。

修订后五项回归再次全部通过，实际源码SHA、argv及原stdio见 `RESULT.actual.json`、`regression.stdout`、`regression.stderr`。原REPORT、ZIP及其检查不改写。本补充无游戏启动，不增加业务信用。
