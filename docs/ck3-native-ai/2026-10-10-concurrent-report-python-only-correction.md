# 并行报告的 Python-only 文本勘误（2026-10-10）

精确 `6baf0b73ecad9bcf9940144093293b6a1d80de4d` 的 [Official CI 38010875810](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38010875810)
在 `Enforce Python-only Windows automation` 失败。校验器自身 **9 项测试通过**；
仓库扫描随后报告 **3 violation(s)**、exit 1。三处均为同一历史内存恢复叙述中的禁止 shell 名称：
`docs/autonomous-agent-progress/daily/2026-10-10.md:305`、`docs/autonomous-agent-progress/weekly/2026-W41.md:2617`、`docs/testing-workflow.md:3473`。精确源文件 SHA、原行文和原失败输出均封存于证据 ZIP。

同一精确提交的共享 CK3 acceptance 步骤 success，
[Linear history 38010875847](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38010875847) success；
Li Yu Dao static checks **NOT_TRIGGERED**，不计成功。本次失败不归因于运行时或缓存测试回退。

最小更正范围是三处历史叙述的 shell/旧命令字样，以明确的历史禁止 shell / 只读文件读取措辞替换；
PID 22976、86.46 GB RSS、99% 内存负载、取消行为及原始回执链接保留，校验规则不放宽。
本包只保全更正前的失败，不包含更正后的校验结果，也不声称新 CI 已通过。

[结果](acceptance/2026-10-10-concurrent-report-python-only-correction/RESULT.actual.json)及[索引](acceptance/2026-10-10-concurrent-report-python-only-correction/INDEX.json)
保存原终态、12 组查询回执、失败原 step、终态 jobs、双 workflow 完整日志和精确原文行号。
ZIP 274553 bytes、50 项，SHA-256 `8aa92157da9aa13656296bd4c75c9ba3c8370d6d2a965634da0700a35cebc984`；
[读回复验](acceptance/2026-10-10-concurrent-report-python-only-correction/ARCHIVE-VALIDATION.actual.json)确认 byte-exact / CRC PASS。
打包未新增 API 查询、测试或主树写入，旧 `b0e5119` 成功与 `6a3` / `0c0e` 失败保持各自来源事实。
