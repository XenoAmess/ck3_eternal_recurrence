# 第一期R7正常闭场后继（1.20.0.4）

R7已通过原版GUI正常退出，并取得独立原生进程OS0、原始run/host/keeper等待及实际屏幕释放记录。这补齐P链和圣物链文档建立时尚未结算的闭场事实；研究holder结束、媒体成片资格与整体业务验收分别记录。

`machine_id: 4-8e1c2f1861`；run `4-8e1c2f1861--faith-and-power--R0007`，CK3 PID20256、create_time1792250472.7258115、creation FILETIME134367240727258115。原生source commit为 `b8be8ca6cb9cc01297a2a6bd318c9b6e09847c2c`，a05 DLL SHA-256 `13126d50051490c29f1c82cf2fd3f1050d8e501c727805f78daf22140a6987ef`。后续合入的源码候选不追认为R7已加载的DLL。本节全部事件时间直接保留来源UTC字段；过程、身份、SHA和边界见[闭场小投影](faith-and-power-episode01-r7-closure.json)。

| 证据阶段 | 来源原始时间 | 实际结果 |
|---|---|---|
| 单次原生confirm_desktop | 2026-10-17T15:55:14.371153+00:00 至15:55:22.223628+00:00 | 一次native submission；返回dispatch_pending，尚未观察退出 |
| 独立observe_normal_exit | 2026-10-17T15:55:26.095433+00:00 至15:55:26.352291+00:00 | 原保留句柄signaled、身份一致、exit_code0、typed_normal_exit_observed=true；无新提交 |
| public run原Popen完成 | 2026-10-17T15:55:39.751339+00:00 | PID16420，actual_original_popen_wait=true，returncode0 |
| host原Popen观察 | 2026-10-17T15:55:39.876761+00:00 | PID16224，actual_original_popen_wait=true，returncode0 |
| keeper报告及allocate原Popen完成 | 报告2026-10-17T15:55:48.250204+00:00；原等待完成15:55:48.363838+00:00 | keeper_actual_exit_code0、thread_exited=true；allocate PID23004原wait0 |
| 屏幕CAS完成事件 | 2026-10-17T15:55:58.949475+00:00 | sequence11459；task faith-e01-shared-a08 done/resources[] |
| public verify原进程观察 | 2026-10-17T15:56:12.787821+00:00 | actual_exit_code2；research_holder_completed=true，business/product-release等资格false |

首次确认的保留句柄等候到有限期限时仍为timeout，即使其中exit_code字段为0，也不能当作退出已观察。后续观察复用同一request/process身份，真正读到signaled后才结算退出；没有重发已消耗的confirm。normal-close记录为 `normal_close_qualified=true/cleanup_ok=true/business_pass=false`，managed process tree和控制资源清理有独立证明。自动保存框由Root按原画面审阅为unchecked；`autosave_verified=false`，本段不授予保存业务信用。

Root另报告overlay工具会话43715实际返回0。本补注只按工具会话报告记账，没有将43715称为OS PID，也没有补造原OS等待回执或精确退出时间。

keeper原件保留四个录制终态，均为 `NORMAL_TREE_EMPTY`、job returncode0、job_active_processes0、probe exit0，结果 `ENCODED_UNREVIEWED`：

| take | recorder终态观察时间（来源UTC） | raw bytes |
|---|---|---:|
| episode01-r7-P-take01 | 2026-10-17T15:35:18.246320+00:00 | 80136142 |
| episode01-r7-relic-take02 | 2026-10-17T15:43:44.925863+00:00 | 72676225 |
| episode01-r7-relic-remove-take03 | 2026-10-17T15:50:51.580819+00:00 | 42794375 |
| episode01-r7-creation-context-take04 | 2026-10-17T15:53:34.258123+00:00 | 24751332 |

四条都仍为 `human_review_performed=false/clean_spans_certified=false`；正常编码收尾不等于人工听审、完整1倍观看或clean片段签核。小投影中的raw引用来自keeper既有回执，本次未重读原片正文、重算原片SHA或重复媒体验证。

本场创建窗口已打开，但Root报告当前 `selected_type_unavailable`，未提交实际Create；不能把打开窗口或后继Create源码资格记为世界新建成功。既有P链、圣物链的局部业务后态仍引用[重规划研究](faith-and-power-episode01-replanning-r7-12004.md)和[圣物成功链](faith-and-power-episode01-relic-r7-12004.md)。其受益者、好感、奉献后态、普通战役成绩及整个产品未完成边界继续保留；本闭场补注不将公共verify的research holder结果升级为whole-product PASS。
