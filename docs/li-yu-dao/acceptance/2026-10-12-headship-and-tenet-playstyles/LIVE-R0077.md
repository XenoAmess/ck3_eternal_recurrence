# R0077：T35 实际操作、T08 准备拒绝与正常关闭

本页记录 R0077 的实际结果，闭账截止为 2026-10-13T00:30:22.572354Z；另列 ROOT 于 00:34:07Z 报告的协调任务释放事实。产品整体仍为 **NOT_GREEN**。CI 成功、启动基线一致及正常退出分别只证明各自范围，不授予制度批准、SAVE 对照、宗主、newT、C3 或 I4 验收信用。

实机来源为 `aeb0a77e2b7fc355a8c7371309fdcfe85a6a193f`，CK3 1.20.0.4、PID 9972，RUN 为 `bf-202609141645-5434332d4d--li-yu-dao--R0077`，CASE 为 `lyd-release012-keypaths-20261013-028`。沿用 Source19 / Native058；AD040 是独立 2 GiB、120 分钟窗口，未续期旧窗口、未提高 cap，也未为此重新构建 native。后来 MAIN 的文档及准备改动不改写本场加载来源。

以下外置原件采用三个路径简称：

- A40 = `C:/workspace/ck3_lyd_runtime_20261004/lyd-release012-headship-not-nand-storage-admission-20261013-040`
- RUN77 = `C:/workspace/ck3-common-runtime/runs/bf-202609141645-5434332d4d--li-yu-dao--R0077`
- A39FIX = `C:/workspace/ck3_lyd_runtime_20261004/lyd-i3b-not-nand-fix-20261013-039`

启动基线实际为正式构建 83 文件逐字节一致、启动 marker 1、fixture failure 0、LYD error lines 空数组。真实初始 Learning 7，入门后为 8；本人礼仪为白沙，ID 174。T35 实际提交 native option index 0，之后 Learning 14，威望 2200→2050。这是已发生的单步操作，不代表后续培养或制度流程通过。

T08 导航被原 30 分钟 preparation phase 的剩余时间门槛拒绝，未执行 T08。原错误为 `Navigation needs 300s on the original phase and more than 900s total reserve`；本次不足的是原 phase 的 300 秒要求，原 deadline 未延长。累计实际提交 6 个 production event options，准备结果为 `partial`。ROOT 于 00:14:44Z 审阅并记录 `Learning14_T08_not_started_original_phase_deadline_no_institution_no_SAVE_no_headship_credit`。本场没有制度批准、SAVE 对照或宗主验收结果。

退出时单次 final 点击返回 `status=rejected-readback`、`failures=["foreground_changed_after_click"]` 并转至 Steam，未重放点击。ROOT 直接审阅新鲜 delayed002 画面及 CK3 空列表；该 GUI review 本身没有声称原进程 OS exit 0。随后保留的原游戏 HANDLE 独立取得 signaled=true、exit_code=0、actual_retained_os0=true，`normal_close_qualified=true`，native managed thread 完成且 cleanup 成功。本场 Source19 实际等待 ROOT review；不能据此声称尚未加载的共享后继候选已经验收。退出界面 autosave 为未选中，不授予 autosave 或主动 SAVE 信用。

原 public run 返回 0，verify 返回 **2**，allocator 返回 0；失败结果保留。最终 Steam 离线画面由 ROOT 直接审阅，显示恢复至 1024×768。SCREEN 从 sequence 5353 释放到 **5354**，实际 release 为 done、resources=[]。ROOT 另报告协调 task 于 00:34:07Z 进入 done、resources=[]、sequence 5355；这是后续协调事实，没有向已关闭的 A40 新增回执。

A40 实际于 00:30:22Z 关闭：charged 581,365,396 B，unused 1,566,118,252 B，carry 138,164,749,746 B，cap 141,327,031,211 B，closing GC credit 0。旧派生文件实际回收为两批共 31 文件、逻辑 3,673,622,531 B，已通过独立 claim 扣除一次；物理释放量 UNKNOWN，R11 保护项保留。不能在本次 closing 再扣这笔信用。

精确 aeb0a77e 的 [Official Runner 38320534972](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38320534972) 与 [Linear 38320534987](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38320534987) 均为 attempt 1、SUCCESS。Li Yu Dao 在该 SHA 为 **NOT_TRIGGERED / NULL**，CLA 为 **NOT_REPORTED / NULL**；不借用其他提交的 run。旧 e57563fb 的四项 normal-close CI 失败保留，后继成功不改写旧记录。

原件索引如下；大 SAVE、完整 native 报告、截图和构建二进制未为本页复制或重新读取。

| 原件（以上述根解析） | 字节 | SHA-256 |
| --- | ---: | --- |
| A40/BASELINE-PROFILE.actual.json | 1229 | `3780341224c0c754a454834ab9f531c54dc01b7f239934b84d2f84069e121ef1` |
| RUN77/case-output/release012-preparation-0011-choice.actual-results.json | 22902 | `8821c626ad2527f0afc00ff426e190bb8d15f56ade97f51582ad6115e695479d` |
| RUN77/case-output/release012-preparation-0013-awaiting.json | 39303 | `9f850552b8f93872d0d6fcb38b7fbafcb3fe82f9ca9fe95b55921cb9cd33285f` |
| RUN77/case-output/release012-preparation-0013-root-result.json | 847 | `8d704083d04d6fa04ad87ce7e85497998d318ec5f274df9a1a8b6345a35c808f` |
| RUN77/case-output/normal-quit-root-result.json | 3599 | `b68f73028d0918e7ad6ca887f436ff40afe871c8cc50d08da8031e754179ff9c` |
| RUN77/case-output/normal-close-result.json | 12513 | `b995d7e75a60aae9a1523d6eac757d1b9d316a9d55ee104f6cfa6e94a06e9231` |
| RUN77/release-command-001/stdout.log | 1360 | `96db84daf9f65ad0418acf6af54bdb2b707c3b02c3bf45f6b563550421a2a754` |
| A40/RESOURCE-CLOSE.actual.json | 23289 | `ef697ada668d1f1f5a19f2f0dc4253b30cfc6aec9030075b521327b31f83c199` |
| A40/CLOSED-RESERVATION.actual.json | 1129 | `259bccfebbeb688b83eb322a68610fd1ca7eaf23de3caa90ce3ba53b382f6528` |
| A39FIX/AD040-CLEANUP-CREDIT.claim.actual.json | 1748 | `f8a95c70ecbc42c08f98204559175f1cde6cceca8ca923da378d0049279134e8` |
| A39FIX/ci-aeb0a77e-001/INDEX.json | 9362 | `08fb9e2b1e5d8b470038eba37f94dac0635e7d30161e2c69fe1459387b8ebc47` |

后继查询节奏已作源码调整：first phase 使用 full readiness；只有明确的 preparation observe 请求设置 `request_full_readiness=true` 时，才在下一 checkpoint 刷新一次。其余 retained 结果保留原观测身份，不能冒充当前状态；final 仍须独立资格核对。ROOT 报告对应 cadence 的 2 项 focused tests 实际 PASS、exit 0、0.010 秒，覆盖 retained、显式一次刷新、final 16→14 拒绝，以及固定 deadline 与 Quit reserve 不延长。它们是本场之后的源码验证，不追授 R0077 live 信用。

下一场 preparation 从 1800 秒调整为 3600 秒目前仅为 **SOURCE_ONLY 计划，未准入、未启动**，R0077 的原时限与 partial 不变。C3 源码补充本人 Learning≥20 对 AI 权重的影响，正常 T15 个人信条培养仍在核对；尚未执行，不记为学习提升、AI 票数或正式批准。
