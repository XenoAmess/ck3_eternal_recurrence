# R0074：择师问道导航与事件选项映射实际 RED

记录发生于 2026-10-12 UTC（本机 CST 为 10-13 凌晨）；本页仅记录已经发生的结果。**NOT_GREEN，无产品业务 PASS。** 正常关闭与公共命令退出 0 不改变业务结论。公开版本仍为 **0.1.1 Alpha 内部测试**；0.1.2 未上传。

证据路径约定：

- `A36` = `C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-navigation-storage-admission-20261012-036`
- `RUN74` = `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0074`
- 以下相对文件名均指这两个外置原件根；未复制 native report、SAVE 或图片正文。

## 实际输入与推进

`A36/ROOT-RUN-BINDING.actual.json` 实际绑定 R0074、CASE025（`lyd-release012-keypaths-20261012-025`）、keeper `20261012-a37`，消费 `public-entry-002/ENTRY-BINDING.actual.json`。`BASELINE-PROFILE.actual.json` 记录正式 production **83 文件**与实际 profile 字节一致；启动 marker 1、fixture failure marker 0、LYD error lines 为空。这些记录证明本场加载基线，不代替业务验收。

本场原始实际 actor **31254**，Faith **31**、main rite **33**、自身 rite **32**、learning **11**；与 R73 的身份状态不同，不沿用其资格。G2 观察保留 active main33、候选30034/learning32、自身 rite32，当前无 eligible；living member count **4702**。ROOT baseline 0001 已实际确认原儒家身份、无 HoF、原礼制与主礼制，以及上述正式 profile 加载。

实际 `lyd.1` native0 入口正常。学派详情 nav3 的支持修复后，第一次“择师问道”入口已实际走通；后续选择发生真实映射错误：

1. ROOT preparation **0005** 针对 typed `lyd.10` 要求 **native8 / rendered7**，意图是看后一页。
2. adapter 错误提交 public `option_number=8`。实际 service 与 native_driver 的公共编号换算均为 **N−1**；原 `0005-choice.actual-results.json` 的 ACK 明确为 `event_selection.selected_native_option_index=7`，不是 ROOT 请求的 native8。
3. preparation **0006** 实际观察 rite **170**、无 active event。ROOT 于 **18:10:34.999644Z** 提交 `abort`，原 note 为 `Observed_school_choice_postcondition_differs_no_replay_no_institution`。

没有重放选择；未继续 institution、SAVE 或后续 150 prestige / 100 gold 付款步骤。本场不授新 HoF、政治继承保护、付费代表项或完整派别矩阵通过信用；误选后的实际状态保持原记录。

## 后续源码修正与实际测试

MAIN adapter 已将目标 native index 换算为 **public native+1**，并核对实际 ACK 的 selected native index。这是后续源码修正，本场未重放、未追认实机修复通过。

`option-mapping-tests-command-001` 实际运行 25 项，exit **1 / errors=1**：新测试的模拟 snapshot 缺少正确 `option_count`，触发 `active_event option exceeds option_count`。原失败回执与 stderr 保留。修正 fixture 后，`option-mapping-tests-command-002` 实际 **25 PASS / exit0**，结束于 **2026-10-12T18:26:43.314826Z**。这是 focused fixture/source 验证，不是新场实机信用。

## 已发生的退出与尚未完成边界

正常菜单退出已实际完成。`RUN74/case-output/normal-close-result.json` 记录 retained HANDLE signaled、OS exit0、native process exit0、cleanup/tree gone true、managed thread finished true、`normal_close_qualified=true`、`business_pass=false`。public run 原回执 actual exit **0**，结束于 **18:28:16.399659Z**。

verify **001** exit **2**，缺少 allocated run context，原错误 `Verify requires one actual allocated run context`。verify **002** 已携带实际 context，仍 exit **2**，原错误 `Reviewed source/admission bytes changed`；MAIN 在本场后已修正源码，未倒改原 source/admission pins。两次 verify 均为 BLOCKED / NOT_RUN / NOT_ASSESSED，失败原件保留。

**2026-10-13 02:50 CST 实际补录**：ROOT 已亲审 18:38:32Z 的新窗口位移画面 A36/final-offline-004/steam-moved.png 与恢复后的 final-restore.png，两图均显示“离线模式”；最终桌面恢复 1024×768，实际读回在 display-restore-002.actual.json。旧 001/002/003 画面准备失败原样保留；Steam 最小窗口在 1024 宽桌面不能满足工具的水平位移余量，004 临时使用 1280×960 取得新图后再恢复，没有切换 Steam 在线状态。

STOP proof 后原 allocator wait actual0 于 18:41:36Z 结束；keeper 实际线程退出、SCREEN 按原序列 5246 精确 CAS 释放于 18:42:59Z。A36/RESOURCE-CLOSE.actual.json 为 21274 B，SHA-256 25a11b03bfd3454accc4a6d2b1b38a26ba8c233b49722a92128354ad6b19738b，独立证明正常资源关闭，不授业务信用。

AD036 于 **18:49:30.499765Z**、原到期 **19:18:21.192520Z** 前实际 CLOSED：peak 805306368 B，charged **519645263 B**（含 MAIN/Git/bus 32 MiB 与收尾 1 MiB 保守份额），未用 **285661105 B** 归还；carry 从 139148442843 B 到 **139668088106 B**，hard cap 139970526427 B，GC 信用 0。CLOSED-RESERVATION.actual.json 保留 public run0 / verify2 / allocator0，SCREEN 已释放、重写入者已停止。关闭器 001 将十一日前的 stale origin/master 任务误纳入资源门，原拒绝保留；002 沿用准入的 fresh active CK3/build/storage 资源范围，未修改旧原件或扩大容量。此后 A36 只读。

## 小型原件 pins

| 原件 | bytes | SHA-256 |
| --- | ---: | --- |
| A36/BASELINE-PROFILE.actual.json | 1231 | `ca0f4d6bb96c05636acc63fa2b5768df5ad2ee9c7b55833e02d2c0645896cab7` |
| RUN74/case-output/release012-baseline-0001-root-result.json | 1932 | `4242706087865977bb219fc63cea9ac4f136128ff53b1f14534e1a965cf02533` |
| RUN74/case-output/release012-preparation-0005-root-result.json | 1053 | `1664dfe160fadd60a5abda10262a152cab38e9286405a3581622ee95029fbc0f` |
| RUN74/case-output/release012-preparation-0005-choice.actual-results.json | 22884 | `eaaea9f17edefa16574f6cf86c7b4c87897d9a91ec936c4f2a593a4993c7cffe` |
| RUN74/case-output/release012-preparation-0006-root-result.json | 1417 | `bdfa5f9bf98c0b01ea555231759c3b4ccd28f8a5e06ee407ce79f305a08db1c5` |
| A36/option-mapping-tests-command-001/RESULT.actual.json | 973 | `38a0690354e6f372d56d603eb4b459f041bfdad64d5ab1206245127e4d019481` |
| A36/option-mapping-tests-command-002/RESULT.actual.json | 972 | `afdbb9f257314be2e4765a1680222bfc3b4bef18d6e192adf627f1b5e08e5c91` |
| RUN74/case-output/normal-close-result.json | 10550 | `fa3dcef528be3421ade3744a880188838b6f2ffe2e61ea7b7986e2336de614bf` |
| A36/run-command-001/RESULT.actual.json | 1846 | `364175bf2bab30114f1ac51a10a2f89eacf2690bc2ff5a918a3a8453f436a0b5` |
| A36/verify-command-001/RESULT.actual.json | 1668 | `05821155160660e84243448e005f47eb73f9f7521ad86bd5a11737ac5724b688` |
| A36/verify-command-002/RESULT.actual.json | 1852 | `0fffbebcb6afdb036392c0db45b2371f2e572ab97445d3078d131400f4b4c70e` |

本文汇总实际 ROOT 操作与小原件；未复制大 native report、SAVE 或图片正文。源码聚焦检查通过不追认 R0074 实机通过。
