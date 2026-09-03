# 天朝二期宣传流水线状态摘要（2026-09-03 13:25）

这是 `df06581` 之后的独立状态快照，专门记录“工具链已可用”和“成片仍未具备”之间的边界。本摘要没有启动 CK3，没有调用 TTS/FFmpeg 编码，也没有生成任何媒体。

## 已闭合

- fresh promo-tool checkout：`Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903`
- 最近一次 `git fetch origin main --prune` 后，`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`，工作树 clean。
- 独立工具测试：`263 passed, 2 skipped`。
- 两版 authoring 文本已经独立落盘且与各自 project config 的 SHA-256 绑定：人物版 `10` 条旁白 cue（`364` 个中文字符）、`20` 条简中字幕行和 `20` 条英文字幕行；制度版 `10` 条旁白 cue（`361` 个中文字符）、`20` 条简中字幕行和 `20` 条英文字幕行。两版均保持 `release_usable=false`，要等真实 source review 才能提升。
- 对上述 draft 文本做了只读字体像素预检：人物版最长中文/英文行分别为 `1104/1010 px`，制度版为 `1104/983 px`；对应当前 `1920×1080` 字幕轨可用宽度为 `1740/1700 px`。这是排版准备证据，不替代最终成片抽帧和两轮人审。
- CK3 的环境启动门现在已有有效 warm profile 证据：无 Mod/无 bridge、当前 Release bridge、RBX guard candidate 均到达 `Frontend` 并以 exit `0`/cleanup proven 收尾；这三轮没有执行 gameplay，也没有产生可入片的二期素材。剩余问题是 Phase2 projection/seed/capture，不再是“CK3 本体完全打不开”。
- 进一步的 Phase2 A/B 表明 b1/case-kernel 与 workforce 左右半截断可启动，但完整 workforce/broad 合并仍在 `Total 881` 后停滞；完整 localization fan-out 已单独验证为 parser=0 但仍未进入 history。故当前不能把任一半截断运行当作完整二期能力或宣传素材。
- `preflight_phase2_media.py` 和 `build_phase2_promo_video.py` 的 Git 身份探针已改为对同一 checkout 使用路径限定的 `git -c safe.directory=<resolved> -C <resolved>`；不修改全局 Git 配置。修复前实际遇到的 dubious-ownership 错误已消失。
- 两版无媒体 preflight 均完成：
  - 人物版 receipt：`_runtime/promo-preflight-character-20260903-1259.json`，SHA-256 `BE74D3D07FF4C79096B6280BCB9D8222D977BBA37B0DAD57A7E2A9BD37AFACD6`
  - 制度群像版 receipt：`_runtime/promo-preflight-institution-20260903-1259.json`，SHA-256 `38817A85A9B5EC97D244B63662CF2CD5965A04F50ADC090D6A59E427F7820770`
  - 两份 receipt 都是 `environment_preflight=GREEN`，并确认工具 HEAD、Pillow、Edge TTS voice、字体、FFmpeg/ffprobe 能力；最终 readiness 仍为 `RED`（`footage_pending`、`publish_target_pending`）。
- 使用真实 preflight receipt 加旧 fixture 做 builder 探针，按预期返回 `RELEASE: RED / footage_pending`，且没有创建 work directory。这证明 builder 会先挡住不合格素材，不会越过门禁。

## 当前阻点（两版相同）

| 门 | 当前状态 | 解除条件 |
|---|---|---|
| 八段二期实机素材 | `0/8`；fixture 缺少 `capture-timeline.json` 与 `loaded_seed_v2` | 在已验证的 warm profile 上完成 Phase2 projection/seed，再于同一真实 seed/save lineage 取得 8 段 clean span，并通过 `zhongguo_phase2_footage_intake` |
| seed / observer / source registry | 尚未形成同一真实 lineage 的 GREEN 组合 | 由 CK3 实机录制产生并互相绑定的非 fixture receipt |
| source review | 未开始 | 每个 cut 各自完成 1× 原始素材审阅并签署 disposition |
| TTS / 字幕 / candidate | 尚未启动 | intake 与 media receipt GREEN 后分别执行；两条 cut 可并行 |
| claims audit / 双轮审片 / export | 尚未开始 | 两版分别完成，不互相代签 |
| publication target / publish receipt | 未提供 | 明确平台、账号和授权回执；不能把本地导出当发布 |

两条目标文件仍不存在：

- `artifacts/demos/2026-09-03/zhongguo-361-phase2-character-led.mp4`
- `artifacts/demos/2026-09-03/zhongguo-361-phase2-institution-led.mp4`

## 下一步与时间估计

1. 在已验证的 warm profile 上先完成 central/workforce projection 与 seed 的唯一槽 A/B；通过后取得共享的 8 段真实 clean span，并先跑 intake（已有可用桌面会话时，录制与整理约 `20–40` 分钟）。
2. intake GREEN 后，两版分别做 source review、promotion、fresh tool receipt、TTS、双语字幕和 candidate；两条线可并行，单条约 `45–90` 分钟，再加人工审片与导出。
3. 最终交付时间不能从当前 `0/8` 和 CK3 启动阻点倒推成固定时刻；任何旧 fixture、一期素材或占位媒体都不计入进度。

详尽命令入口见 [`recording-command-card-2026-09-03.md`](recording-command-card-2026-09-03.md)，Git ownership 修复与测试证据见 [`promo-toolchain-safe-directory-fix-2026-09-03.md`](promo-toolchain-safe-directory-fix-2026-09-03.md)；CK3 warm-profile 分层证据见 [`ck3-startup-recovery-live-evidence-2026-09-03.md`](ck3-startup-recovery-live-evidence-2026-09-03.md)。
