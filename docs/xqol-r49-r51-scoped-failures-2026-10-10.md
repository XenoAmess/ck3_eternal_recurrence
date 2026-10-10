# QOL R49–R51 原失败与闭场范围（2026-10-10）

本轮三场业务验收均未通过，原 public run/verify 均实际返回 `2/2`，全部 `business_pass=false`、`product_release_pass=false`、`case_acceptance_pass=false`。R49 同时首次实际验证了 Source13 的 initial-plan-error 失败保留闭场路径；R50/R51 取得正常关闭资格。这些生命周期结果不授业务或发布通过。merit 场尚未 allocate、未启动。

以下时间均为 UTC。唯一现场执行者是 `/root/qol_scene_operator`；`ROOT-FIELD-RETURN-01.json` 于 `2026-10-10T03:00:17.263900Z` 记载三场关闭、当前 CK3 进程空、screen 已交回 Root、业务重跑 0 次。记录保留原失败；后续修复仅用于新的 prepare 输入。

## 三场原结果

| 场 / case | 实际范围 | 原关闭资格 | 实际 OS / keeper / allocator exit | 最终 CAS |
| --- | --- | --- | --- | --- |
| R0049 / ordinary_async / a149 | 实际 accepted=2、refused=0、pending=false；原 1/1 断言 FAIL | `failure_lifecycle_completed=true`；`normal_close_qualified=false` | 0 / 0 / 0 | 8083，done/resources[] |
| R0050 / ui_tail / a150 | seq3 精确模板拒绝，未执行点击；业务不完整 | `normal_close_qualified=true` | 0 / 0 / 0 | 8094，done/resources[] |
| R0051 / administrative_appointments / a151 | collector hello schema mismatch；provider 未提交 | `normal_close_qualified=true` | 0 / 0 / 0 | 8110，done/resources[] |

R49 的原公共 host 为 RED；R50/R51 的 host 为 GREEN 仅代表其受管生命周期状态，case collector 与业务结论仍为失败/不完整。三场保留原 public `2/2`，没有把退出 0 或 host GREEN 写成业务通过。

## R49：原 2/0 失败与 Source13 失败闭场首次资格

原日志实际得到 accepted=2、refused=0、pending=false。low 角色仍活着，但已离开原 Catholic/roman faith/rite，与事件 ROOT 的 faith/rite 相同，且没有原 refusal opinion；low 为实际 ROOT 的 courtier。完整实际 ROOT 为 Song `han_8052` / ID 34422，low ID 65810。因而是原 low 样本没有确定地产生拒绝，不能改原 accepted1/refused1 断言，也不能强制回复或改生产 AI 接受政策。

原 initial plan 读到两条禁用 FAIL 标记，保留 `ValueError: result matches.1.line_count expected 0, received 2`。本场没有清理错误或继续业务；Source13 将这次真实 initial-plan-error 保留并进入原 hold，随后原模板自动化完成合法 Quit To Desktop。原实际 native process_exit 为 0（`02:29:24.035463Z`），保留的 OS synchronize/query handle 也实际 signaled/exit 0。

随后原 `acceptance-failure-exit-finish-hold` 在 `02:29:26.581463Z–02:29:27.490893Z` 实际完成：`hold_finished=true`、`failure_preserved=true`，同时保持 `business_pass=false`、`normal_close_qualified=false`。host managed thread 完成于 `02:29:29.920758Z`；原 keeper 与 allocator 均实际 exit 0，最终 CAS8083 done/resources[]。这只授 Source13 该失败生命周期的首次实际闭场资格；原 `strict_native_zero_proof_present=false` 与 `normal_close_qualified=false` 保留，不能勘误为普通正常关闭 PASS。

自动化 actor 是 `template-automation`，`human_review_claimed=false`，没有伪造人工审阅。ordinary 的低分资格修复只影响未来输入：使用原版 `ai_will_not_convert` 因子并增加 D0 原生潜在接受 score guard；原两次接受的场和 1/1 断言原样保留。

## R50：seq3 精确像素拒绝

seq3 `action-0003-template-click/result.json` 真实状态为 `REJECTED_NO_REPLAY`：`click_attempted=false`、`click_completed=false`。原 controller 错误为 “Current target is absent, ambiguous or no longer the exact reviewed pixels; no input”，并保留 `deadline_unchanged=1791601560.447054` 与 `no_replay=true`。

同场只读像素差分记录目标 crop `[58,401,122,432]` 的 1984 个像素中有 3 个像素变化，合计 3 个颜色通道各差 1，最大通道差为 1。此记录没有推断语义变化，也没有放宽原精确像素门槛、再次点击或改写拒绝结果。故未完成业务验收。

本场原正常 GUI Quit/native cleanup/process_exit 0 与 retained OS handle exit 0 成立，原 normal finish-hold 实际成功，keeper/allocator 均 0，最终 CAS8094 done/resources[]；只授原正常关闭资格。

## R51：hello 字段合同错位，provider 未发

原 `case-snapshot-0002` actual hello 有 `pid=12388`、`connection_generation=1`、`expected_ck3_version=1.20.0.4`、`expected_ck3_sha256=98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`、`game_adapter_id=ck3-1.20.0.4-msvc-x64`、`game_adapter_status=ready`、`ck3_build_match=true`；没有旧 collector 查找的 `game_version`、`executable_sha256`、`bridge_pid`。实际为 collector 对 hello schema 的读取错位，不能据此称游戏版本或 EXE 不匹配。

原 sequence0 `appointment-full-pool` 的 request 与 once-intent 已落盘，但 eligibility proof 在 provider 提交前拒绝，保留 `ValueError: Appointment collection rejected: eligibility proof requires exact executable`。因此没有实际 provider 执行、完整候选池、分数分解、继承者切换或其他任命业务 PASS。已有请求/intent 不能充当已调用或已验收。

本场原正常 GUI Quit/native cleanup/process_exit 0 与 retained OS handle exit 0 成立，normal finish-hold、keeper/allocator 均成功，最终 CAS8110 done/resources[]；只授原正常关闭资格。Root 因已知共用 collector 问题，在 allocate 前暂缓 merit；`NOT_ALLOCATED_NOT_LAUNCHED` 必须保留，不能记作 merit FAIL 或 PASS。

## 原预算与后续边界

| case | command | readiness | total | hold | poll |
| --- | ---: | ---: | ---: | ---: | ---: |
| ordinary_async | 300 | 400 | 4500 | 600 | 0.05 |
| ui_tail | 300 | 400 | 3000 | 1800 | 0.05 |
| administrative_appointments | 300 | 400 | 3000 | 1800 | 0.05 |

以上均为原 entry-run-result/host argv 的实际预算；没有延长原 hold、扩大总时限或重跑同场业务。normal GUI Quit、失败 finish-hold 和资源释放在原预算内完成。

PAM baseline、ordinary D0 资格、新增原 L2.4 领主共享钱包赎囚，以及任命 hello schema 的必要修复均只可形成后续新输入。新 prepare 不是业务 PASS；必须使用 Root 采用后的 clean HEAD 与同一公共执行底座。保留 R46 已 valid 自付及 R48 同场只读 supplement 的既有范围，不重复已通过场，也不从单 case 外推全产品/发布资格。

## 冻结来源

外置路径缩写：`C10=C:/workspace/ck3-upgrade-20261010`，`LIVE=C:/workspace/ck3-upgrade-20261004/live`。native-report 只保留原 receipt 给出的 pin，本次没有展开大 raw scope 或将其写入文档。

| 来源 | 实际路径 | bytes | SHA-256 |
| --- | --- | ---: | --- |
| ROOT_FIELD_RETURN | `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/ROOT-FIELD-RETURN-01.json` | 9445 | `8a2a1a48f896fb043dbc26660568376416b53fa9ab8f28817617554c751be5c7` |
| THIN_SOURCE | `C:/workspace/ck3-upgrade-20261010/resume-qol-02/r49-r51-doc-01/R49-R51-THIN-SOURCE-01.json` | 51358 | `447fecf445fe431cdbb597a6cbc3ff33da5b04271d6a0905e8e11c3e3a3f69ba` |
| R49_DIAG_THIN | `C:/workspace/ck3-upgrade-20261010/resume-qol-02/r49-readonly-watch-01/R49-THIN-005.json` | 7479 | `b0c2ed29de0c721f1f2995848ebf50d9f7332aa138f0ea2b696a6e14e746d7d0` |
| R50_SEQ3_TEMPLATE_RESULT | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/case-output/ui25/action-0003-template-click/result.json` | 2861 | `b053a4056a489dd2a40a66917af6b566c17668f6cccb446cdf6633eb79500dc9` |
| R50_CONTROLLER_ERROR | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/case-output/ui25/controller-error-preserved.json` | 211 | `d4a956f12713f729b2d8489091b500a3cb47526a52c476b07e0a7c78bbefb473` |
| R50_PIXEL_DIFFERENCE | `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/R50-TEMPLATE-PIXEL-DIFFERENCE-READONLY-01.json` | 405 | `03a82105dfd47dba6d819f9bc7bf45006991673a8612811f33a433a626cf8607` |
| R51_HELLO_ACTUAL_STEP | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/case-output/case-snapshot-0002.actual-results.json` | 56817 | `3f3e4940d4f7934109436f4cab7c66d88708b4938d9f96422c7e030f2fc5e370` |
| R51_COLLECTOR_ERROR | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/case-output/case-error-preserved.json` | 236 | `73b2700519431db6e28394aff7d98198f0a3e68161055c98b98924630a30dd0f` |
| R0049_CLOSE | `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/ordinary_async--a149/POST-RUN-CLOSE-05.json` | 3643 | `50615f56668a66994e4807c139aa4871a9f3f3d250144baa88045fc71311765a` |
| R0049_PREPARED | `C:/workspace/ck3-upgrade-20261010/qol-ordinary-source13-diag-attempt30/prepare/prepared-case.json` | 25516 | `fb8df9b3f81c2d37ba044c7fd5a9c037b2b943848b31a1ca60a08316458af9a9` |
| R0049_ENTRY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0049/case-output/entry-run-result.json` | 48869 | `ee19ebd2d41ce2829a64faa16bdd2120288cb3b4407277c8ca4ee2fafa644a2a` |
| R0049_NORMAL_CLOSE | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0049/case-output/normal-close-result.json` | 30527 | `61e2b6be222e0e8a58ee4cf9e6afddf1c784d4471f538be5a5207a2b038a64a5` |
| R0049_NATIVE_REPORT_PIN_ONLY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0049/native-report.json` | 36109707 | `acb4c2ab01c5501cef25a9ebf2de2167250d1e7cd4eda5f54eb1654b861cb350` |
| R0049_FAILURE_FINISH_STEP | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0049/case-output/acceptance-failure-exit-finish-hold.actual-results.json` | 3487 | `06a0ad5b413e37209fc0b6eb92a67b3162b02ee5e6c9085b09066f16ab8eb2b6` |
| R0050_CLOSE | `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/ui_tail--a150/POST-RUN-CLOSE-05.json` | 3586 | `f58124098024cd4a6b870067010c30241d8b6d0fa6e39e09b08c5ddf3589e175` |
| R0050_PREPARED | `C:/workspace/ck3-upgrade-20261010/qol-ui-source12-attempt23/prepared/prepared-case.source13-manifest-canonical-25.json` | 25239 | `7372f43973efd667ab3c5a9eb238a5a41533aba518a1ca9d7c1c220cf245d311` |
| R0050_ENTRY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/case-output/entry-run-result.json` | 54251 | `1c21a12c20325f944719905ea4b903f4a427ff078a6cb68414479a457bbfaa50` |
| R0050_NORMAL_CLOSE | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/case-output/normal-close-result.json` | 28965 | `180d585142250488b5f82577f7932f14ee2ef2a3fcdec595e3ed8914ae9305b0` |
| R0050_NATIVE_REPORT_PIN_ONLY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/native-report.json` | 39293564 | `a6ebe17f047e36316278bce77a9b2404715d097fdb7c7f86aaefed2998290d5b` |
| R0050_NORMAL_FINISH_STEP | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0050/case-output/acceptance-normal-exit-finish-hold.actual-results.json` | 2491 | `8347128390bd1c1be74e99d5383898a65ca58e831e419afeef2a7e0d8cbc305a` |
| R0051_CLOSE | `C:/workspace/ck3-upgrade-20261010/qol-scene-resume-02/administrative_appointments--a151/POST-RUN-CLOSE-05.json` | 3691 | `f0459984680e6ae2445cb1a09d039780138559de54f2f19d7fc98478ee9f1be6` |
| R0051_PREPARED | `C:/workspace/ck3-upgrade-20261010/qol-three-source12-prepare-19/attempt20/administrative_appointments/prepared/prepared-case.source13-manifest-canonical-25.json` | 25642 | `ac5746d0e27486f97a3e526aee6e83c4b8d5ac1833da7cb1327225dab26e80e6` |
| R0051_ENTRY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/case-output/entry-run-result.json` | 46885 | `62be2931e7409cfcc6e570d6de4806bc7e824e4a39d14ee34e693b6914771339` |
| R0051_NORMAL_CLOSE | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/case-output/normal-close-result.json` | 29322 | `a911ddf70dd0feab9c4ea33938235ced8893ee34e9af13bebe97a9124398ed21` |
| R0051_NATIVE_REPORT_PIN_ONLY | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/native-report.json` | 37454134 | `324cb637f671d4e359c34bd6f422d9854826f600842f423ce484ac2dde3b25d5` |
| R0051_NORMAL_FINISH_STEP | `C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0051/case-output/acceptance-normal-exit-finish-hold.actual-results.json` | 2668 | `2091ce9d602662e1cf1aaef95767f1b4ce864a414bfd0d58e13371a0fcb3bc27` |
| COMMON_RUNTIME | `C:/workspace/ck3-upgrade-20261010/root-source13-adoption-01/runtime.adopted-source13-native-fd1f-queue04-05.json` | 10820 | `a5aecdf94d6e3dcf35f2462011ba6a743668605729627f6d272542cf8c460e91` |
| SOURCE13_MANIFEST | `C:/workspace/ck3-upgrade-20261010/shared-source13-prepare-01/SHARED-RUNTIME-MANIFEST-SOURCE13-NATIVE-FD1F-01.json` | 46108 | `26b229556f0b97cfac3b7d0172dd55f97f39f410c476de97f01a0eb1c5361c18` |
