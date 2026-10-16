# E04 R188：11 日片段与 pre-resume hook 失败

本记录只封 R188 的第一段已终结原片：原生精确完成 11 日，1067 年 3 月 20 日至 3 月 31 日（`53148792→53149056`）；第 12 日只完成 Arm，录制阶段没有提交 Resume。prepare-only 子进程约 3 秒超时，observer 未 Start；录像在 finally 中正常 finish。片段未达到 100 秒要求，新增 clean、业务正例与人工签收均为 0，动态视频资格仍 0/11。原生天数不等于已直接审阅的可见天数。

机器 `desktop-3fevhd2-1c74096080`；run `desktop-3fevhd2-1c74096080--vanilla--R0188`；源/native 构建来源 `d05b0c780b615faa714fdf0535403bb2e6941faf`。实际绑定 PID `12060`、creation FILETIME `134366470385086412`、generation `1`、episode `native-31254-0a8ceff1be59`、角色 `31254`。实际版本 1.20.0.4/build 25734779，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。来源场次 `D:/workspace/ck3_native_war_ai_promo_work/e04-r188-window-capture-a01`；实际时间 2026-10-16 UTC（北京时间 10 月 17 日）。

加载阶段的两次身份未就绪分别保留：17:58:16 的 a01 snapshot 返回 `is_error=true`、native state unavailable；18:00:36 的 a02 snapshot 返回 `is_error=false`，但 `map_ready=false`、`played_character=null`、`episode_run_id=null`，未通过上层身份条件。不能把两次都称为 SDK 错误。18:03:50 的 a03 已读到 map ready/角色/episode，18:04:05 独立绑定 guard PASS；保存的身份链对本次 PID 生效，不把历史角色数值视为通用映射。

sampling admission 对自然与 payment 采样各 enable 一次，并独立读回 enabled/epoch 1/awaiting sample；这些开关与 ACK 没有证明付款或补员业务。单次 recorder Start 于 18:08:53.277310，ready 到首 Resume ACK 为 3.6012072 秒。11 份完成回执及对应原生 sentinel status 均保留，均 triggered、零 overshoot。18:09:22.435099 的第 12 代 Arm 目标为 `53149080`（4 月 1 日）；hook 随后失败，所以本段只计 11 日。

hook 声明外层预算为 15 秒，实际失败来自 prepare-only 子进程固定约 3 秒的 `TimeoutExpired(..., 2.9999924001749605)`；hook 总耗时约 4.0903673 秒。原错误、claim、fresh window 与 Root finalize 原件均保留。Root finalize 2704 B / SHA `5c10bd2de098016244e8bed0c08a7586f5bb14a823ca2471e88d05defde91cfb` 明确 `NOT_STARTED_NO_OBSERVER_START_CLAIM`、SDK calls 0、observer restarts 0，不能写成 observer 已安装或恢复成功。

原片 `raw-window-a01/raw.mkv` 为 17,888,946 B / SHA `bfea8ea5ab9cbd8daf16e5f86a86d45d261fa41e053eab3d83638acae7fb6cb7`。UTC wall 为 34.031147 秒；monotonic wall 为 34.0311703 秒。媒体审计为 914 帧、30.466 秒、1280×720、无音轨；完整 AV decode exit 0 且 stderr 为空，无 premature-end。正常 `NORMAL_TREE_EMPTY`/returncode 0/Job active 0 证明录像收尾，不能替代整个 CK3 会话正常关闭。100 秒条件未满足，仍是未获资格的 partial。

捕获源是 `gdigrab desktop` 中客户区矩形 `[640,360,1920,1080]`，输出 1280×720；这是桌面像素中的客户区区域捕获，不是 HWND 直接捕获，也不是整桌面录制。source guard 原回执无错误，原 audit 的三张抽帧 `visually_reviewed=false` 历史保留；追加 Root 有限直接审阅回执（6419 B / SHA `c433d00fc9256bc2cb5378fd63b1a1cf02a76bd0bf1fe8a59efe6897218cec31`）记录：首帧 Mar20 暂停，Army18 面板 1173/1%/300/300；中帧 Mar25 运行、面板 1162/1%/300/300；尾帧 Mar30 暂停、面板 1162，中央“已宣战”原生通知覆盖地图且右侧有领土被围攻 toast。三抽帧均报告无桌面/其他应用像素。尾帧可见 Mar30 不能因原生第 11 日到 Mar31 而改标；有限三帧审阅不构成全片 clean、完整 1×、业务结论或签收，也不据面板差值推断兵力损失因果。

Root 随后在同 PID 下的跨月业务救援必须单独记录。已终结 raw 的时长、帧与可见内容不会因后续业务增加；本包封装时未包含后续跨月成果、整个会话 normal close 或 screen release，也不制造这些成果。研究 6/14、业务 4/11 的既有口径不变。

便携小证据见 [source-index.json](evidence/episode04-r0188-20261017/source-index.json)与[分阶段事实](evidence/episode04-r0188-20261017/facts.partial-a01.json)。保留 exact originals 与来源路径/SHA，以及代码的 HEAD/blob/SHA/CRC pin；原片、PNG、存档、二进制、部分大响应与完整依赖仅留来源 pin，没有声称完整可移机验收闭环。其他机器应重新核实自己的身份、版本、Steam、权限及容量。封装未运行游戏/SDK/桌面、未重跑测试或修改主仓；记录按通用存储策略 1.0.0 的 record 周期复核。
