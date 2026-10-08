# Exact HEAD fa0f5e1ee 官方 CI 终态

HEAD **fa0f5e1ee098ab6fab4635bedce939eab857610a**；parent `57ee1192ce932782a3ae19732db35cba3fe14971`。第一次官方查询时三个 workflow 已终态，run/job/check 结论一致。

| Workflow | 实际结论 | Run / Job | Job UTC |
| --- | --- | --- | --- |
| Official Runner CI | FAILURE | [37756034825](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034825) / [113240689583](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034825/job/113240689583) | 2026-10-08T09:21:08Z → 2026-10-08T09:28:11Z |
| Linear history | SUCCESS | [37756034901](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034901) / [113240689381](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034901/job/113240689381) | 2026-10-08T09:21:08Z → 2026-10-08T09:21:50Z |
| Li Yu Dao static checks | SUCCESS | [37756034997](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034997) / [113240689958](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37756034997/job/113240689958) | 2026-10-08T09:21:10Z → 2026-10-08T09:22:08Z |

Official Runner 实际 **FAILURE**，唯一失败步骤 **#41 Test disposable fixture engine identities**（09:28:06Z），官方 annotation 只给出 `Process completed with exit code 1.`。具体失败用例、producer stdout 和详细原因均 **NULL**；完整 joblog NULL，下载尝试0，不据此前失败猜原因。本次 **RMTM #31 SUCCESS**，后续 skipped 步骤原样保留，不能称整个 Official CI GREEN。是否由本次改动导致或属于其他来源亦 NULL。

Li Yu 本次真实 **TRIGGERED / SUCCESS**。官方 PushEvent `23358727551`（push_id `45829969467`，UTC `2026-10-08T09:21:05Z`）before `57ee1192ce932782a3ae19732db35cba3fe14971` → head `fa0f5e1ee098ab6fab4635bedce939eab857610a`；官方 compare 一提交、57路径。exact workflow blob `f383249db0221ddd4b6d4a3aa4d44c9d4c6de7b6` 的 push filters 匹配 `mod_li_yu_dao/tools/build_factory_diagnostic.py` 与 `mod_li_yu_dao/tools/validate_factory_diagnostic.py`，原件和完整路径清单见 `TRIGGER-PATHS.source-facts.json`。

本轮 10 次只读官方 API GET，读取失败 0 次；response、回执和结构化 steps 按原字节保全于 INDEX/raw ZIP。没有重查旧487/8c结果或将其外推为本次fa0；没有 MAIN/Git/runtime/system 设置动作、本地 tests/build、workflow rerun/dispatch。

此包只提供该 exact HEAD 的 CI 事实；新 native DLL/live/formal/newT/C3/I4 信用 NULL，whole mod **NOT_GREEN**。待ROOT现场正常闭合后按 candidate 复制清单 create-only 入库；本轮没有导入 MAIN、commit 或 push。
