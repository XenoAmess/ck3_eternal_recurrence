# E04 R188：原片终结后的跨月观察与闭场

这是已终结原片之后、同一运行时的独立追加记录。原片仍为 11 日/34.031147 秒 wall/30.466 秒媒体，未达到 100 秒要求；后续跨月的一日不进入该原片，动态视频仍 0/11，新增 clean、业务正例、人工签收均为 0。

机器 `desktop-3fevhd2-1c74096080`，run `desktop-3fevhd2-1c74096080--vanilla--R0188`；源/native 构建来源 `d05b0c780b615faa714fdf0535403bb2e6941faf`。PID 12060/create FILETIME 134366470385086412/gen 1/episode `native-31254-0a8ceff1be59`/角色 31254。来源为 `D:/workspace/ck3_native_war_ai_promo_work/e04-r188-window-capture-a01`；下列实际时间为 2026-10-16 UTC，即北京时间 10 月 17 日凌晨。

Root 在原片终结后处理独立 monthroll 观察，继续原第 12 代 sentinel，实际从 Mar31 `53149056` 到 Apr1 `53149080`，原 g12 triggered、completed tick 1、零 overshoot。没有重授这一天为原片天数，也没有重启录像。`NATURAL-DAY.actual.json` 7265 B / SHA `289d6eac5df0db6b035961a0940117e425d4998444aa7501c69fe790b1323dc0` 绑定本次 Resume 与后验。

观察器保留的原 raw 为 34982 B / SHA `d20028e2596ea585939c033cde5ace26f804e51c7bcb8b0ccec11d06478f9a0b`；strict projection 6891 B / SHA `05575043e9ca43c0469bbbfe9d3ec74e902daf62d6778e4ce010fd1db754262d`。它确认两次 qualified 物理写，分别针对 `+0x2c0`/`+0x2c8`，值为 469493→469493、0→0，均为同值写；post RIP RVA 为 `0x28a645b`、`0x28a6466`。原 projection 的 producer/source 仍 unknown、maintenance attribution unclosed，当前小包没有补造 body 归因。`+0x28`/`+0x30` 没有保留样本不构成 absence；窗口有限且不是所有写全覆盖。terminal restored/detached/cleanup complete 均 true、pending event false，原 raw 与 projection 均保留。

Root 的 `r188-natural-after-a01.json` 查询实际成功：`accepted=true`、`observed_history_full_v1`/`exported_retained`。5366 B / SHA `b95bd4a2a87296a83ee18bd70d106a5296af4021945b491a2dd40928334ca049` 的 compact 结果位于 `body.armies[0]`；后续 Root 断言误读 key 不能改变这次 SDK 成功，也不应重放查询。

沿该回执唯一具名 `raw_result_reference` 读到并复核 full Driver 原件 `state-a01/native-session/army-query-history-results/army-query-5e1bb82b14e34577b092c3bcc2b7f142.json`，12280646 B / SHA `69c9655e63c658a494ceb4f855bd8925b63e0c093e9cda2c6839c9ccdf0c9afb`。完整结构使用 `army_strengths[0]`，不是 compact 的键。它是完整 Driver result，不是原 pipe bytes；本次离线提取没有大 raw glob 或 SDK 重跑。

该 full 结果的 Army18 `actual_loss_writer_observations_v1.event_count=0`、`events=[]`，全局 oldest 2131/latest 2642/overwritten 2130。因此 selected actual-loss 样本为 0，不能凭空添加正例，不能证明没有损失发生。另有 24 条自然 parent records；当前 Army18 1162/1195、siege loss budget 11 是当前输入/状态，不是“实际写了 11 人损失”的因果证据。包内保留带完整 JSON pointer 的精确解析子树与首尾自然 parent 上下文，清楚区分派生选择与原始文件。

18:26:46.183174 实际 normal save：4445 B / SHA `dae7f83597044ab02d4dab7ce14fa3c097f42c2ca959efb213fe6aeeb7d45336`。checkpoint 为 74492850 B / SHA `13d0724240bd341ec2e88f92ee50d0deb2cd1189ae1ef2803a16e34bc86c74be`，只保留原件 pin。18:27:59 bootstrap 记录最终游戏 `process_exit`/exit 0/session ok，SDK 线程退出、supervisor/keeper 无错误、final sequence 5841，进程树 gone/cleanup proven、recorder `NORMAL_TREE_EMPTY`；18:28:00 Root launch wrapper exit 0。screen release 原回执已另附于本包；其具体返回值应以 exact 原件为准。

[小证据索引](evidence/episode04-r0188-monthroll-20261017/source-index.json)、[实际状态](evidence/episode04-r0188-monthroll-20261017/facts.monthroll-close.derived-a01.json)与[具名 Driver 选择](evidence/episode04-r0188-monthroll-20261017/driver-selected-loss-context.derived-a01.json)供视频与开发/决策复用；[原片阶段](episode04-r188-window-capture-12004.md)保持历史不变。研究 6/14、业务 4/11 的既有口径不变。其他机器仍须重核自己的机器状态；只读提取和小原件封装不构成目标机器实机资格。
