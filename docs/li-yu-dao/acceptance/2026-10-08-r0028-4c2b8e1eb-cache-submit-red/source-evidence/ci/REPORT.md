# Exact HEAD 4c2b8e1eb 官方 CI 终态

目标 **4c2b8e1eb496ae9167dd23b88fbff3ec9a84b60c**；tip parent `5a9d6d876de67ab080755535e40516fd21e69e09`。只读官方API保存本HEAD实际自动push run/job，初始pending原样保留，最终结论如下。

| Workflow | 实际终态 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | completed / success | [37719933003](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37719933003) / [113125022824](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37719933003/job/113125022824) | 2026-10-08T02:51:43Z → 2026-10-08T02:59:04Z |
| Linear history | completed / success | [37719932906](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37719932906) / [113125022403](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37719932906/job/113125022403) | 2026-10-08T02:51:43Z → 2026-10-08T02:52:20Z |
| Li Yu Dao static checks | NOT_TRIGGERED / NULL | NULL | NULL |



Li Yu **NOT_TRIGGERED / NULL**，不是GREEN。本次Linear原producer显示实际event范围 `35ddda4ee4531709a69371a05f493e90ad4ef993..4c2b8e1eb496ae9167dd23b88fbff3ec9a84b60c`；官方compare实际 ahead 3 / behind 0、40个路径，没有任何路径匹配exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6` 的四项push过滤，最终exact run list亦没有LiYu run。tip本身仅5个docs路径，未把tip变化冒充整个push范围。源码/native/SDK来源仍必须以各自实际资格和后续live验证授信用。

本轮 15 次只读证据读取尝试，read error / timeout 7 次：原urllib连接重置、Official日志30/45/60秒CLI超时、public日志HTTP403均保留，不改写为成功；Python fallback的gh凭据读取10/45秒超时，尚未发起HTTP或实际使用token（003原回执的通用路由flag不代表凭据成功取得）。读取重试不重跑workflow。**Linear完整原日志已成功取得一次；Official完整原日志仍NULL**，其六次读取失败回执保留，此文件只封实际CI终态和当前归档边界，缺失日志以后只能新增补档。具体见 `LOG-ACQUISITION-BOUNDARY.source-facts.json` 和 `TERMINAL-AND-ARCHIVE-BOUNDARY.actual.json`；`FINAL.actual.json` 是实际CI终态，不表示全部日志取得。

原API/stdout/stderr/exit回执与SHA都在 `INDEX.json` 和 `raw-evidence.zip`，必要解包核验见 `ARCHIVE-CHECK.source-facts.json`。没有重看旧c791日志、重跑CI、dispatch、MAIN/Git/SDK/CK3/进程/Steam/屏幕/总线、本地测试或构建动作。CI不代替新DLL/live/业务/正式批准/newT/C3/I4/typedexit验收，whole mod **NOT_GREEN**。
