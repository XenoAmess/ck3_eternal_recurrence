# Exact HEAD 487da05f6 官方 CI 终态

HEAD **487da05f6c1cf231490fd1fe480ccc704ed0a80f**；parent `2b1f502ef8335a9ed16aa794bc3db7907f554f8a`。本包只读此 exact HEAD 自动 push 的官方 run/job/check 及结构化 step 原件，初始 pending 保留。

| Workflow | 实际结论 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | SUCCESS | [37733161493](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37733161493) / [113166674725](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37733161493/job/113166674725) | 2026-10-08T05:35:43Z → 2026-10-08T05:44:42Z |
| Linear history | SUCCESS | [37733161599](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37733161599) / [113166675060](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37733161599/job/113166675060) | 2026-10-08T05:35:44Z → 2026-10-08T05:36:21Z |
| Li Yu Dao static checks | NOT_TRIGGERED / NULL | NULL | NULL |

实际失败步骤 0；完整 step 原件在 FINAL 和 API raw 中。没有以旧 8c 成功、source focused 或本机构建结果代替新 487 CI。

Li Yu **NOT_TRIGGERED / NULL**，不是 GREEN。官方 exact PushEvent 未取得，push before/full push filtering 为 NULL；tip parent 与其路径独立保留，不当作 push before。 exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6`；原件与路径依据见 `TRIGGER-PATHS.source-facts.json`。

共 11 次只读官方 API GET，传输/API读取失败 0 次，原始回执、response 和异常全部保留。此前 API 暂未收录此次 exact PushEvent 的结果亦保留。按本轮范围，完整 joblog / producer stdout **NULL**，下载尝试0。

`INDEX.json` 和 `raw-official-evidence.zip` 保存原字节及 SHA，单次解包字节校验见 `ARCHIVE-CHECK.actual.json`。没有 MAIN/Git/runtime/system 设置变更、本地 tests/build、CI rerun/dispatch；native/live/正式业务/newT/C3/I4 信用 NULL，whole mod **NOT_GREEN**。旧 8c 包未写入。
