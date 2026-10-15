# R0177 海岸正常准备、S0 与闭场

machine_id: `desktop-3fevhd2-1c74096080`。本包编目时间、原小回执精确 SHA 和运行时身份见 [canonical summary](acceptance/2026-10-16-r0177-coastal-normalprep/SUMMARY.actual-a01.json)。实际运行 source 为 d9322bcfb3e17a3fe78607cea777bbfaf7be0a11；正常闭场回执记录于2026-10-15T21:02:43.641386Z，exit0、game/recorder/SDK keeper 已关闭、source freeze 已释放。当前源码后续整合不追认本场旧二进制能力。

Army93/native85 经正常 Move 和自然推进到2624，date53146848，空 route、regular、paused、非交战；独立 full query 为250/250、4团/4 DATA、stock10000000。正常保存的 common S0 是71631396 bytes、SHA `e6ee95c3184c00989af660c5d765a27622fd5b93f9e8930fdc5a5ed56e157d67`，已按原回执另存保护副本。它是 pending R07 两个 fresh-load arms 的输入；不是旧 episode_seed，也不是后来的 terminal checkpoint。保存时另两支己军94/95在战斗，此事实保留。两 fresh arm 完成数0、treatment_started=false、R07_PASS=false。

海岸原片为45.000秒、1350帧、2560×1440@30、H264 yuv420p、无音频；59607616 bytes、原 recorder SHA `88f37c5911ffa25491122c2f11dd04b3c17aeecdc0ff6f72605df77e3530231d`。现有媒体回执记录一次 probe 和一次严格全解码通过、6个同支样本实际审阅。本包只读取指定小回执，不重读或重hash视频/存档，不重复解码、seek 或重编码。

剪辑候选为0–4秒移动中、4–10秒转换括界、10–15秒抵达后短对照、15–43.5秒暂停留屏备选。画面状态变化仅限定在 `(4,10]` 秒；精确首次状态变化 PTS 未知，业务 phase done 的 wall time 不能替代首次像素 PTS。独立原生抵达与媒体候选分别保留来源；完整 cut 表及原样媒体报告都在 [小原件 archive](acceptance/2026-10-16-r0177-coastal-normalprep/r0177-coastal-small-originals.zip) 中。

连续 clean、人工1×、human signoff 均false。此正常准备/媒体技术通过不增加整卡计数，本包沿用5/14＝35.7%；R03实际资格由其 owner 的独立包记录。媒体小原件部分历史文件没有 machine_id，保留原 bytes；SUMMARY 依据 exact runtime proof、report.run_id 与 code-index PID/create/generation/episode/actor 一致追加机器身份补注，没有按路径猜机器。

[可复用代码索引](../../promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0177-coastal-code-index.actual-a01.json) 链接现有生产/视频入口，并将本场两份 scene verifier 与绑定输入的精确源码封存在 archive 中供检查和改写复用。它们包含原场专用路径，不能直接重跑已完成的媒体扫描或外推跨机运行事实。新机器可复用知识与代码，须另提供和绑定其 own raw/S0/runtime；本包未复制视频、存档、DLL或JPEG样本，不提供完整 raw replay。

外置保护与容量仍受原 active32MiB 分配和 `2026-10-16T07:45:01.597Z` 复核点约束，本次不续期。原小回执、原错误与原状态均未覆盖。
