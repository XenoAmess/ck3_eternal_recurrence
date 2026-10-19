# C5 自然窗口补充

机器 `xenoamess-full-tower-eb9d2c1186`；闭窗结束 `2026-10-19T06:14:20.215501Z`，分析 UTC、全部小输入 SHA 与生产器见 [回执](evidence/c5-closed-persistence-analysis01.json)。复用已冻结 C4 解析 helper，未改 C4、旧账本或生产源码；0 新 RPC、0 Driver/SAVE 正文读取。

持久化仍不是这段的主要耗时：3 次实际全量写入共 0.0158058 秒，succession、life、事件选项各一次；候选 run 为 `0→1→0`，被事件选择 full barrier 关闭。历史部分从 1,329,562 字节/164 行增至 1,553,028 字节/181 行，包含多个延后查询；不能归因某一条，也不外推长期。现有 WAL 没有已验证的连续 append 省写机会，保持关闭。

281 提供普通事件提前打断的实际样本：目标 8 日，实际 3 日，`active_event/source=native`；sentinel generation7 仍 armed 时合法 cancel 返回 accepted/canceled。AUTO 为 2.8818131 秒，driver life 为 2.4300574 秒，此次没有旧约 30 秒尾部。283 查询事件，285 已按共享 registry 执行选项3；这只覆盖此次事件等待，不授所有变体或整批验收。

计时标签存在复用：7 条 `driver.life_advance_public_change_wait` 合计 2.5456674 秒，但最后 0.2407112 秒位于 AUTO285 的事件选择后验内；真正包含于281 life区间的是6条、2.3049562秒。不能仅按标签把全部 public wait 加到 life。阶段相互嵌套，均是墙钟，不是 Native CPU。

263 的 612,270 字节响应只有 oversized 元数据，没有 tiny timing header；其耗时仍未知。MET262→264 的 5.896678 秒还包含该 RPC，不当作队列间隙。FULL258 已知27个子RPC及未归因余量在回执单列；不把余量全归显示或轮询。

累计截至 FULL258 失败：AUTO9 起 10,050.794575 秒/110 日，SDK115 起 8,401.147434 秒/92 日。C5 仍从首次失败 AUTO255 的 `06:00:38.447748Z` 起算，含修复为 821.767753 秒/3 日；不重置到成功 AUTO259。FULL258 自身为 19.060659 秒/3 日，其中原 MET286 返回后到外层失败还有 5.040468 秒。

只结算13个cycle，98→111。AUTO285 和原 MET286 已成功，显示 ACK 失败使112仍待结算；不重放、不赠送cycle或天数。封存时还记录闭窗后开放维护，留到后继累计。当前没有长期吞吐达标。

生产命令：`python -B tools/g2_saved_campaign/analyze_c5_closed_persistence_v1.py --output <新回执路径>`，输入固定小来源、SHA和机器，输出 create-only。解析是自然证据核算，不是 benchmark。
