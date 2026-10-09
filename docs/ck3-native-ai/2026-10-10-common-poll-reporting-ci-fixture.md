# 公共轮询报告的 CI 测试夹具修复（2026-10-10）

精确提交 `6a3affdb87f03f01bdc9f4dc43aeff15960200db` 的
[Official Runner CI 37995375811](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37995375811)
在 `Test shared CK3 acceptance without installed CK3` 失败。
`tools/test_ck3_mod_acceptance_poll_reporting.py` 的 6 个测试均报
`NameError: name 'supervisor' is not defined`：测试经 AST 提取生产 host 的 `write()`，
但测试 namespace 没有提供该函数新增使用的闭包变量。
同一提交的 [Linear history 37995375808](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37995375808)
成功；Li Yu Dao static checks 为 **NOT_TRIGGERED**，不计作成功。

生产 host 已在声明 `write()` 前初始化 `supervisor: threading.Thread | None = None`。
本次只给隔离测试 namespace 补入 `supervisor=None`，与该初始状态一致。
实际 `write()`、6 个原测试及断言继续执行；生产 host、清理及退出行为未改。

| 实际命令（Python 3.13，`-B -X utf8`） | 运行位置 | 结果 |
| --- | --- | --- |
| `tools/test_ck3_mod_acceptance_poll_reporting.py` | 精确 6a3 原文件外置副本 | 6 ERROR，exit 1，同 CI 异常 |
| 同上 | 单行修复外置候选 | 6 / 6 通过，exit 0 |
| 同上 | 应用修复后的本仓库路径 | 6 / 6 通过，exit 0 |

外置复现前，两个测试输入文件（test 与 host）都与精确 `6a3` 的 Git blob 字节核对一致；
本仓库确认时，测试文件与已验证候选逐字节一致，host 与原副本逐字节一致。
命令、时间、stdout/stderr、源码 pins 与真实返回码见
[实际结果](acceptance/2026-10-10-common-poll-reporting-ci-fixture/RESULT.actual.json) 和
[证据索引](acceptance/2026-10-10-common-poll-reporting-ci-fixture/INDEX.json)。

全部 31 组原始 GitHub API/命令回执、终态 jobs、失败日志、两个 workflow 的完整日志 ZIP、
原版与候选测试输入及修复前后回执封存于 `raw-evidence.zip`（393927 bytes，SHA-256
`de32007049488e04f1996d2924106eb3e21146a828862d0186b4c1a70ab444de`）。
[读回复验](acceptance/2026-10-10-common-poll-reporting-ci-fixture/ARCHIVE-VALIDATION.actual.json)
确认全部 131 项 byte-exact、ZIP CRC 正常；原始日志经 ZIP 保留，避免 Git 文本换行归一化改变证据。
此包不重复封装 Source04 runtime。

本次未启动 CK3、Steam、keeper，未领取屏幕或写真实 run ID/admission。
这是 Python AST 测试夹具修复，`open_kaishek` 预验为 not-applicable。
本地通过不追认精确 `6a3` 的官方 CI 成功，也不授予公共 runtime 或产品实机 GREEN；
后续以新精确 master 的官方 CI 终态为准。历史失败与旧报告保留。
# Rebase integration note (2026-10-10)

After this candidate was tested, concurrent `origin/master` supplied `supervisor=threading.Thread()` in the same isolated namespace. Integration retains that remote thread object rather than replacing it with the archived `None` candidate. Both provide the missing closure variable; the archived before/candidate/repository receipts remain historical bytes. The final rebased fixture is checked again after resolving this actual overlap. This note does not change the failed exact `6a3affdb8` CI result.
