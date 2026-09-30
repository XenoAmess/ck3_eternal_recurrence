# a04 增援章节逐句证据核对（2026-10-01）

42 句已逐句核对：41 句在正文声明的范围内有据，r038 的机制说明有据，但主图日期及人数标签错误，需修图。没有发现需要撤回的增援机制断言。完整中文句子、具体 claim、来源绝对路径及 SHA、画面与原生字段的场次/日期/对象关系见 [utterance-audit.json](utterance-audit.json)。这不是完整人工审片或 clean-span 签核。

原始 A01 `trace-finish` SHA 为 `A688CC0C656364914BE5E42457C0DCCE94415A83163950BF68F1021D9A907CA5`。本轮重新计算了 11 份原始材料（含 1.325 GB 原片）和 5 份原版静态文件的 SHA，全部与旧事实 ledger 一致；独立逐行读取 old side0 27 行、side1 24 行，确认九字段均不变，返回缓存残差均为零。原生三点均为 CombatID 16777218、ArmyID 22、date 53146512、thread 20844；final width 1480→2220，首次 side0 出伤参数 2220。

真实原图直接可读的是 12 月 14 日 893/1603、海牌 2570，以及 12 月 15 日 827/4106。A01 可见图没有 2560、Q 原始账或战宽 tooltip；UI map 的 exact_frame_pts 为 null，所以只证明同 run、对应日期，不能说 UI 像素已绑定到 join hook 瞬间。r012、r016 诚实区分同入口残差与跨日死伤；r025 区分数学半数和定点中间值；r028 把森林 0.9 标为静态来源；r035 的 54.055% 明确是公式复算。

唯一标签错误在 `project/review-story-a04-board-specs-v2.json#/utterances/reinforcement-r038/ui_label`，以及 `project/review-story-a04-edit-v2.json#/utterances/reinforcement-r038/spec/ui_label`：主图为 raw-365.000.png，实际 12 月 15 日 827/4106，标签仍为“12月14日｜我方893／敌方1603”。应改成“12月15日｜我方827／敌方4106”；extra_ui 的前日 893/1603 正确保留。旧 a04 图和成片已直接审阅，未改动。

最小补采为两个当前 run 暂停帧，各绑定原生 snapshot/control、原始全图、人数与战宽 tooltip。原版 `window_combat.gui:646` 的相对军力条使用 `CV_TT_RELATIVE_SOLDIERS`；`combat_window_l_simp_chinese.yml:65` 明确包含双方人数与 `GetCombatWidthBreakdown`。它提供具体悬停目标，现场是否呈现仍须实际审图。推进后一日暂停帧的逐团 current 已可能承受主阶段伤亡，不能冒充 join 返回值；新 run 的数字要现场读，不强迫复现旧 A01。

J-d11 没有补拍素材：a12 原生暂停准入/退出完成，但镜头位于错误区域且有 ToDesk 遮挡；a14 在 `STOP_CURRENT_FOREGROUND_IS_NOT_THIS_RUN_CK3` 处停止，录制 NOT_STARTED、raw_video null；a15 仅 `STATIC_READY_LIVE_STOP`。可复用 a15 的当次 PID/HWND 焦点验证、原生 camera center、三个新原图布局门和唯一 SDK 的 MCP 准入。未修改的 a15 continuation 会录 600 秒并最多推进一日；若要缩成两帧补证，需要新冻结的有界 consumer，不能虚构旧 CLI 已有无录像 advance。

具体输入、入口及逐点验收见 [minimum-supplement.json](minimum-supplement.json)。本轮未操作 CK3、桌面、Steam 或 OneDrive，未 fetch/pull/merge/rebase/cherry-pick，未提交或推送。过程材料保存在 `C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-01/`。
