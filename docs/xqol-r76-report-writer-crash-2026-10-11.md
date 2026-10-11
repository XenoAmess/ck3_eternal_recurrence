# QOL R0076：报告写入故障与最小修复

实际记录：2026-10-11 13:37 CST。范围仅体验优化与重整河山的 1.20 迁移，361 不参与。

## 实际失败

`4-8e1c2f1861--xenoamess-quality-of-life--R0076` / `administrative_appointments--a179` 使用冻结 Source18。共享 host 在替换 `native-report.json` 时发生 `PermissionError: [WinError 5]`，原报告停留在 unfinished；公共 run/verify 均为 2，行政任命没有业务 PASS。CK3 与原 harness 随后已不存在，不能把独立资源清理写成正常关闭、OS0 或产品验收。

原件：`C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0076/harness-stderr.log` 与同根 `native-report.json`。失败停机回执位于 `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/administrative_appointments--a179/EMERGENCY-REPORT-WRITER-CRASH-CLOSE-01.json`，SHA-256 `86045afc044b08efd1ab607945f7fc0282a2b08f95c6f2f8658bc95fccc90b41`。keeper 随后实际退出，原 screen 经 CAS 8682 释放为 done/resources=[]；存储闭账另有实际回执后追加，不提前声称完成。

自有 `more` 诊断分页器仍引用该报告，是待清理的读进程；尚未证明它是这次写入失败的唯一原因。后续读取采用短时完整读取并先关闭句柄，再解析或展示，不对活跃报告分页。

## 最小共享修复与验证

仅将已有 Windows WinError 5/32/33 替换重试从 20 次（最多等待 0.95 秒）延长为 401 次（最多等待 20 秒）。其他错误立即失败，耗尽时仍保留原报告、完整 partial 和错误上下文；不改游戏业务、native、case 预算或旧失败结果。

实际命令 `tools/.venv/Scripts/python.exe -B -X utf8 tools/test_ck3_mod_acceptance_poll_reporting.py` 于 2026-10-11 13:34 CST exit0：16 tests / 1.308s。新增三项直接执行生产函数：200 次暂时拒绝后成功、非瞬态立即失败、401 次耗尽保留失败证据。其余既有检查只随这次小型定向文件执行一次；这是合成故障验证，不是实机恢复证明。

Source18 冻结原件不修改。后继公共 runtime 需独立小型冻结、绑定和新 single-use prepare；未完成前不宣称修复已进入实机。

## 并行调整及下一门槛

新增四条互不冲突的并行工作：R76 失败资源/存储闭场、共享 writer 最小修复、QOL 剩余输入执行卡、重整河山构建/更新说明准备。仅本机 CK3 启动/桌面串行。下一实机优先 PAM 正例，其后继续两类任命与赎回；重整河山两份 Source17 输入未运行，须为选定公共版本准备后继绑定。

截至本记录，QOL 关键业务 case 仍为 2/6（33.3%），重整河山为 0/2（0%）；两产品本次 Workshop 发布均未完成。代码修复、草稿和资源清理不增加业务百分比。

原外置失败证据因未解问题限期保护至 2026-10-18，届时按统一存储策略复核；该日期不是无限续存承诺。

## 13:37 CST 之后实际资源闭账

独立资源闭场 `FAILED-ATTEMPT-RESOURCE-CLOSED-01.json` SHA-256 `22b63d78509ad301d7eeb964ec782ad62b6476d3ea2beb02884121a36f61474b` 位于上述 a179 attempt。原报告和 partial 保留；只停止了 root 自有、精确 PID/创建时间绑定的 `more` 与 `cmd` 读进程。存储闭账位于 `C:/workspace/disk-cleanup-20261010/resume-05/storage-coordinator/admin-a179-source18-45-after-r75-cleanup-gzip-reservation-52-closed.json`，SHA-256 `7f2659f4ca58a6cc74b0bc5b2701de45885b43d4fe1757572b77d84270918e92`；新增保守 allocation 346,479,784 B，当前项目上界 35,954,853,520 B，闭账时可用 28,668,366,848 B。原场预约已释放，不等于新增可用磁盘；下一场仍须独立容量准入。

随后发现原 `case-output/actual-retained-handle-os-exit.json` 已证明 CK3 原 PID 8932 的 retained exit 为 **1**（不是 OS0）；先前行政资源回执中的 null 仅表示当时尚未读取该原件，须用独立勘误追加，不覆旧原件。原 harness 的 retained wait/退出码仍没有证据。下一公共分配需要显式失败资源闭场路径，不能假称标准完成或跳过前场闭场门。

共享公共入口已新增显式 `--previous-failure-close`，仅核验这类真实 writer 崩溃后的行政资源闭场：冻结输入、原报告/错误、原客户端及 keeper/allocator 的真实等待、实际非零 CK3 retained exit、原 host 身份消失、当前无进程 blocker、exact CAS 释放和控制文件已清。该路径保留 `original_host_exit_code=null` / `original_host_wait_proven=false`、非正常退出、业务/发布 false；原正常关闭门和 graphics-cache seed 门不放宽。

新增九项直接生产函数检查最终一次 9/9 PASS / 1.338s。第一次真实 R76 输入绑定暴露 manifest 路径斜杠表示差异，最小修正仅规范化路径比较，bytes/SHA 继续 exact；随后真实绑定 PASS、runtime blockers=[]、旧报告 SHA 前后不变。独立勘误 `FAILED-ATTEMPT-RETAINED-EXIT1-CORRECTION-01.json` 的 SHA-256 为 `f0567aa710915ecdb366a5847fc49a9e8efaa5a6b6b39e52ce00f4a1967819a2`，下次 allocate 必须显式传它，不得把旧报告修成 finished。
