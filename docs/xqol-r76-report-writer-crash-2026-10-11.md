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

## 13:52 CST：Source19 实际冻结与两产品公共准备

修复包已 rebase 并普通推送至 master `1a9be0f1b55bab887c4d83ecc6d6afac2b195470`。新公共 source 仅把已验证的 `write_atomic_report` 函数投影进冻结 Source18；其余 6,905 文件同卷硬链接继承，native/provider/caps 不变，不复制当前 master 整份 host。

第一次物化在 canonical host 函数位置映射失败，`pause_campaign_after_advance` 是类方法，原 producer 仅遍历 AST 顶层。原 `shared-source19-report-writer-ready-01` partial 与 `SOURCE19-ORIGINAL-FAILURE-01.json` 保留 FAIL；独立预约已失败闭账。最小后继通过完整 AST.walk 按原 name+range 匹配，十项均找到真实定义、无 legacy 项，九项函数字节不变，writer 范围仅增加四行。第二次实际物化 exit0 / 6.163s，独立逻辑写入 3,470,618 B，16MiB预约闭账且无物理回收信用。

已选定共同 runtime：`C:/workspace/ck3-upgrade-20261010/shared-source19-report-writer-ready-02/runtime.future-source19-report-writer-01.json`，17,281 B / SHA-256 `46b46bbaeb5ae5b2d66ad4207dfd11df43237dcf7a3cb69612140a63d53e1ce2`；manifest 59,321 B / SHA-256 `53dbd92dff1a8d53d227343b4684bf0e1dadf9fc6f160f9be63510abe76ef04a`。完整 source-index 为 3,110,279 B / `8c0b8ff62f6e73b9c346ac526e0f511780e633717356a0abf31b3be515531b4c`。实际成功 close 为同根 `OWNER-DIRECT-DISK-CLOSE-01.json` / `d1598023c2cf78cc62fb7b9092c8e01d85861a8edcbecbc926b2ef94a0ca3dc8`。

PAM+ 未消费43输入仅另建 manifest sibling，原 state/fixture/35步/12日/时间预算不变；新 prepared 位于同根 `prepared-siblings/xqol--pam_positive/prepared-case.json` / SHA-256 `b16d56c277475ee9a429b3c9c969fba8585565a73bad7e3a6f7275c2daa303e2`。新组合公共 plan 实际 exit0、blockers=[]，尚未 allocate/启动。

重整河山两份未消费 Source17 输入同样另建 Source19 siblings，原 core58 / threshold62 个 profile 文件 exact、不复制或重 prepare。新根 `C:/workspace/ck3-upgrade-20261010/rmtm-source19-unused-prepared-siblings-20261011-01`，core prepared SHA-256 `7353badc987b77198d784867bf263e3413fb27b6bf19c5a7bbc083df4bed6ad9`，threshold prepared `a24363a732c87a18f5128b6910c0b78cc06a15bc47fdd4e611018cff6b5860b4`；总回执 `RMTM-TWO-MANIFEST-SIBLINGS-READY.json` / `20d7f44a2de130ee0716d15adf3e6107bc6e10565e642bc3ccf601ae3279f7b4`。两次公共 plan 各实际 exit0/blockers=[]，总逻辑 105,076 B，在128KiB小包上限内，仍无新实机/发布信用。

当前下一场容量仍待准入。旧占用台账不能外推为现可释放量；已按精确根核到多份旧缓存早已空，大目录实际远小于历史值，没有据旧排行强删。相邻完整 PAM− 场次原闭账 allocation 为305,077,272 B、logical442,699,599 B，可用于新场估计复核；任何新峰估算须保留实际依据、最坏超时风险与原 safety/system-growth，不改写旧2GiB预约或把估算变化称为回收。

## 14:24 CST：精确回收、无损归档与下一场估算

旧 native01 的3,760个生成缓存、144个编译中间文件及1,437个干净源码文件，已按原生单链接身份分七批（每批不超过1,000文件）实际回收，随后仅对内容已空的精确旧工作树执行 Git-aware remove。各批及收尾均 exit0/CLOSED、failures=[]；累计原生 AllocationSize 释放274,244,944 B，不将并发影响下的整卷空闲差额当作精确归因。小型回执 `C:/workspace/disk-cleanup-20261010/resume-05/native01-exact-reclaim-small-handoff-259.json` / SHA-256 `8a2db66b3fddf5cb9d9f3847dfeb0b228df24b3114f298d56f3691293ab78f53` 关联全部原始批次与 child wait/exit。

旧 `C:/workspace/ck3-upgrade-20261001/native/source-d19e794` 与其 worktree admin/index 现已不可读，没有同名替代证据。精确源码已由实际推送并回读的 `archive/storage-retention-20261011/native-source-d19e794` 保全，tag object `f7a69d0be5f52736089f0c128ce7ae8927f45c22`、peeled commit `d19e794041eae408666702a1039bde41639cbf6f`；176,643 B retained Git tree 与原构建 recipe 保留，可在新外置路径重建。保护理由是精确源码可恢复，复核日2026-10-18，不等于无限期保留整个历史执行树。SAVE、当前Source18/19输入、DLL/EXE及原始验收证据未纳入该批回收。

另以独立256MiB/600s预约执行旧QOL R1–R56的30份无损gzip（24份transport、6份raw report）。实际child exit0 / 5.48s、30/30恢复字节数与SHA-256相等、failures=[]；原allocation148,021,248 B，archive allocation6,406,144 B，净释放141,615,104 B（未扣小型报告开销）。`C:/workspace/disk-cleanup-20261010/resume-05/old-qol-exact30-lossless-gzip-239-01/actual.json` / SHA-256 `bf2fe245aac8b6246478ef3fee2e9660e7c561b686790128e97e0b078eeae0c4` 保存逐项原身份、archive映射、恢复SHA/字节数与期限。对应旧raw路径现已不可读；恢复时必须解压到新文件并校验原SHA/字节数，不能把gzip路径或新同名文件冒充原件。R60/R71/R73–R76与当前输入不动；gzip不重置资料期限。预约行政闭账及新场准入另外保存，不以压缩成功代替。

仅下一PAM+/a180批准新1GiB场次峰估算，依据相邻完整PAM−实际305,077,272 B及R76失败闭场346,479,784 B；旧2GiB历史不改，6GiB系统增长/20GiB安全余量不减，原35步/12日、timeout4500/hold600等合同不变。长超时日志密度仍可能超估，必须在实际live/state/attempt三根启动Guard251：原生文件身份union去重、区分既有基线与新增delta、30秒采样、750MiB或卷余量门槛/不可观测即通知root正常收场，不给未完成场PASS。251八项模拟自测通过，尚不代表实场监测已启动。

另一条窄metadata线仅找到旧QOL R13–R17五根shadercache候选，去重allocation789,999,600 B；保护路径无交集，但尚未完成用途/期限/占用复核、未删除、没有释放信用。摘要 `C:/workspace/ck3-upgrade-20261010/root-parallel-continue-236/qol-old-state-cache-summary-01.json` / `1a3e74d883ab56fb77164f9752493b69c6fb93db84da44257054240e26bb2e8a`。不为此重复R57–R75已空缓存检查或全工作区扫描。

业务进度仍QOL 2/6、重整河山0/2；本节全部为基础设施与存储事实，均不构成新实机业务或Workshop发布完成。
