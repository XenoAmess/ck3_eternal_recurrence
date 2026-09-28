# 第二期六章 composer 最小入口

2026-09-28，无屏幕技术准备。项目 composer 是 `war_ai_promo.episode_two_second_half:compose`，按当前正式 [xar-promo v0.2.1](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest) 的 `plan`/`build --composer MODULE:ATTRIBUTE` 合同实现；它只读取同一 native run 已保全的音频、六段 chapter reel、来源稿与九张计算卡。六章已有跨两次 TTS run 的 EdgeTTS **剪辑代理** 21:47.472；尚无六章 reel、最终声线或完成的英文字幕审阅，不存在可通过的真实成片 plan/build。`plan` 是只读，`build` 必须用新 workdir，均不启动 CK3 或发布。

## 已完成的无 run 编辑门

用本 worktree 的 `integration/src` 作 Python import 根目录，已执行：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m war_ai_promo.episode_two_second_half --editorial-check --config D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\project\promo-project.json --draft D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\narration-script-draft.md --cards-dir D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\cards
```

上述编辑门回执属于较早的稿件版本：当时 e2 稿 SHA-256 为 `7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3`，九卡目录为 `FD3D3A9EBC39CB43B09BEE6864CDC9A765C53826AF05DC45DCAE1CB49AE8160E`。当前六章 TTS 使用修订后的精确稿 SHA-256 `6F970C3C144646F6ACC74B113E1886AA537563045A48D2F041F1F74B6581EB6E`；编辑门只读，不进行视频渲染、游戏接入或 TTS。

## 真正的生产输入

先在**新** xar-promo native run 内保全六类输入，保留每一步原件、命令、probe、stdout/stderr、失败 partial 与哈希：

1. 精确 `ProjectConfig` snapshot 由 `start-run` 创建；额外保全当次正式 `narration-script-draft.md` 为 `episode02-narration-script`。录音前须按新实机轨迹校对每个数字、ID 与口读，更新稿并在新 run 冻结。composer 要求每章 `zh` 字符串与该冻结稿的**旁白段落**一致，不读脚注、画面指令或来源路径。
2. 九张独立计算卡的 `calculation-cards.json` 和 SVG，artifact IDs 为 `episode02-card-index` 及各自的 `episode02-card-<ID>`。E2-02/03 属追击章 004；E2-04/05A/05B/05C 属骑士章的四条分轨；E2-06/07 属增援章 085；E2-09 属终局章 024。若新录制轨迹改变数字，先改卡源 JSON、重建 SVG 和旁白，再冻结**新** run。
3. 六章已测时音频 `audio.<chapter-id>`，连同原 TTS native run、render manifest、每段 request 与 `response-events.jsonl`、版本、`ffprobe` 与字幕边界分别保全。前四章代理来自 a02，后两章历史研究板代理来自 a03；两者不能合称同一次 TTS run 或正式配音。默认声线为 EdgeTTS `zh-CN-XiaoxiaoNeural/-12%`，必要改声线要记新 run。每章还要有实际英文字幕文本并另行人工审阅。
4. 经 CK3 adapter 只读验过 raw、report、timeline、evidence index、marks 和 clean spans 后，剪成六条 1× chapter reel `reel.<chapter-id>`。每条 reel 的私有 `reel-receipt.<chapter-id>` 记录精确媒体 bytes/SHA/时长、捕获 span 的 attempt/save/raw/control/clean-span 与来源卡标记审核回执。不同 attempt 的镜头只在明确可见来源卡和分隔处接合，不接作同一段连续游戏。计算卡以**全屏独立插页**放进 reinforcement/terminal reel；字幕安全区 `y=1120..1439` 不覆盖原版 UI。当前旧录像不能用来证明新回放的逐日数字。
5. 最后保全 `episode02-production-inputs-v1` JSON，schema 为 `ck3-war-ai.episode02.production-inputs.v1`、`human_signoff="not-provided"`，包括上面源稿/卡 SHA 与六章有序行。每行 `id`、`title`、`zh`、`en`、`speech_duration_seconds`、`duration_seconds`、`audio_artifact_id`、`reel_artifact_id`、`reel_receipt_artifact_id`；时长来自本 run 的音频与 reel probe，不能沿用初稿 29:50 占位码。

composer 读取上述 run artifact，重新验 SHA、章节次序、旁白全文、九卡回放分区、reel bytes/时长、音频测时和来源回执字段。每章成为一个 `SegmentDraft`，2560×1440/30fps，用已保全的 reel 视频和已备的配音生成中文与英文字幕，最后合成**未混主题曲**的 `episode-02-second-half-unmixed.mp4`。主题音乐、固定增益、完整解码、字幕/色彩/PTS、人工 1× 观看与精确文件签核属于后续独立门，不能从 composer 成功推断。

实际用当前 CLI 对单独的 ProjectConfig 做一次只读 `plan --validate-only` 入口探针，返回 exit 2、`Episode 2 needs a native run with preserved production inputs`；这是预期拒绝，且 `workdir` 未创建。它证明显式 composer 可被 CLI 装载，也明确说明纯配置与计算卡不足以生成影片。

本模块故意**不负责** chapter reel 的剪接与画面验证。reel 制作者必须按真实 clean span PTS 截取、顺序保全每个 FFmpeg 调用/partial；插入静态计算卡可按明确给定的展示时长编码，但不能把游戏录像变速、循环、插帧或补尾。reel receipt 的声明须有逐帧/可见来源卡审核来支持；composer 的 JSON 字段校验本身不证明卡真的可见。缺这一层时，正式 `plan` 应停在生产输入不齐，而不是生成占位成片。

## 新 run 时的 CLI 形状

新 run **前再次查当时最新正式 release**、同步 requirements wheel URL/SHA、验证所选解释器与 editable 项目包指向同一工作树，并冻结配置字节。当前此隔离 worktree 没有相对 `.venv`；上面的编辑门使用了显式主 worktree 解释器和当前 `integration/src` 作为 import 根。正式构建优先建该工作树的相对 venv。完成屏幕取材和上述保全后，用 v0.2.1 真实 CLI：

```text
<verified-python> -m xar_promo start-run --run-id <NEW_RUN_ID> --run-directory <NEW_EXTERNAL_RUN_DIR> <FROZEN_PROJECT_CONFIG>
<verified-python> -m xar_promo preserve --run-manifest <NEW_EXTERNAL_RUN_DIR>\run-manifest.json --artifact-id episode02-narration-script --collection raw --role script <FROZEN_DRAFT>
<verified-python> -m xar_promo plan <NEW_EXTERNAL_RUN_DIR>\run-manifest.json --workdir <NEW_BUILD_WORKDIR> --composer war_ai_promo.episode_two_second_half:compose
<verified-python> -m xar_promo build <NEW_EXTERNAL_RUN_DIR>\run-manifest.json --workdir <NEW_BUILD_WORKDIR> --composer war_ai_promo.episode_two_second_half:compose --offline-tts
```

实际还需对卡、音频、reel、回执和 `episode02-production-inputs-v1` 分别 `preserve`，上面的命令不能在缺素材时直接用作构建。`--offline-tts` 让 build 只消费本 run 准备的精确音频；不会调用 provider。每次 build/audit/review 重试使用新 run/workdir，并永久保留旧 attempt。专题正式门、OneDrive 单文件交付和人工签核按系列规则另行完成。

## 六章实际组装入口与精确输入

`war_ai_promo.assemble_episode_two` 是本项目的正式组装入口。它只接收本 run 的已保全素材，外置 `--attempt-directory` 必须是不存在的新目录。执行顺序为 `validate`、只读 `plan`、`build --offline-tts`、单一主题曲固定增益混音、六章元数据复制、ffprobe、完整解码，以及将候选 MP4 再次 preserve 到同一 native run。argv、stdout/stderr、probe、输入 SHA/长度、失败事件和 partial 均留在这个独立 attempt。成功状态仅为 `TECHNICAL_CANDIDATE_UNREVIEWED`；没有人工 1× 签核，也没有 OneDrive 传输或外部发布。

组装还需分别量测未混音乐影片与终片的**视频、音频各自流时长**，与六章总时长在 150 ms 内一致。仅检查容器总时长会让循环主题曲遮住过短的原始旁白音轨。该检查不证明旁白内容正确或整片无静音；仍要完整听看。

保全 `episode02-production-inputs-v1` 时，在已有字段外必须加入本 run `project_config_sha256` 与 `project_config_bytes`；`narration_script_sha256`/`narration_script_bytes`；`card_index_sha256`/`card_index_bytes`；九卡 `card_sha256` 和 `card_bytes` 字典；`replay_by_card`；以及本 run 单一音乐的 `music_artifact_id`/`music_sha256`/`music_bytes`。每一章的音频、reel、reel receipt 还需各自的 artifact ID、SHA-256 与 byte length，例如 `audio_artifact_id`/`audio_sha256`/`audio_bytes`。composer 会把这些声明与 native run manifest 及配置快照的实际字节逐一核对。

真实 production 的每章还必须把 `prepare_subtitle_inputs.py` 输出的 `sentence_boundaries` 和 `tts_source` 合入该章输入行，并按其 `preserve-plan.json` 将两份原 TTS native run、两份 render manifest、六段 MP3 和每段 request/Edge events 保全到**组装** native run。composer 对原 run/artifact、每段 request/event 精确 SHA/长度、逐句文本、单调时间边界、音频覆盖、冻结稿和章音频 SHA 逐一复核；`terminal`/`closing` 的 `historical-independent-replays-candidate-only` 边界必须留在 render manifest、request 与章输入。每章 `title` 也必须与 ProjectConfig 的 `zh-CN` 标题一致。真实输入缺少 Edge 边界时 `plan` 直接拒绝；仅显式 synthetic smoke 可用合成字幕等分回退。

2026-09-28 对现有 a02/a03 作了无 FFmpeg 来源审计：外置 `D:/ck3-research-artifacts/episode02-subtitle-inputs-20260928/attempt-03/` 的 fragments 含六章 **146** 条 Edge `SentenceBoundary`，preserve plan 列出 **70** 条来源文件；`verify_subtitle_inputs.py` 对原文件复核 GREEN，实调字幕引擎得到 330 条中文短 cue，并拒绝改写首句文本与历史使用范围的两次负向试验。审计状态严格为 `machine-source-checked-not-human-reviewed`，`assembly_run_preservation=not-checked`；这些文件尚未保全进六章组装 run，也没有声称听审、英文字幕审阅或成片。

reel receipt 的每条 `capture_spans[]` 必须写出 `attempt_id`，实际冷载存档 `cold_load_save`、raw video、control 的 artifact ID、SHA-256 与 byte length，以及 clean-span 与来源标签审查 artifact ID。运行中另存的 checkpoint 只能放在可选的 `midrun_checkpoint_save` 三字段，不能替代冷载来源；004 的冷载是 45CCE7…，第 27 日 F085… 是运行中生成的 checkpoint。`cards[card_id]` 必须有卡 SHA、replay、该 replay 的 `primary_receipt_sha256` 与 `evidence_mode`；若卡目录声明 `source_save_sha256`，还须对应 `indexed_cold_load_save_sha256`，004 卡另须 `indexed_midrun_checkpoint_save_sha256` 分别绑定两份存档：

每条 span 同时记录原始 raw 的 `raw_video_width`/`raw_video_height`、`upscaled_to_reel` 和 `resampled_to_reel`；reel receipt 记录 `reel_width`/`reel_height`。只读 `plan` 校验这些字段与已保全素材的 SHA/长度，不创建 workdir 或调用媒体探测。实际 `build` 在新 workdir 内对 audio、reel 和每条 raw 调用 FFprobe 并保存 argv/stdout/stderr，校对声长、reel 的 2560×1440/30fps、原始分辨率和上采样声明；不从最终 2560×1440 推断原生拍摄分辨率。组装回执逐条列出原始和输出尺寸，1920×1080 源被上采样时必须明确为 `upscaled_to_reel=true`。

- `historical_research_card` 仅对应冻结的 004/039→040/020/070/036→038/085/024 旧研究回执；还需 `visible_label_audit_artifact_id` 与实际 `visible_label_text`，标签写明“历史研究”、该研究编号、“非当前录制”，审查回执绑定 reel SHA 和卡 ID。
- `current_run_recomputed` 必须先按新拍 attempt 重算数字、重建卡与旁白，再给出 `recomputed_receipt_artifact_id`。该回执绑定新卡 SHA、来源主回执、捕获 attempt 与实际冷载存档 SHA；旧 024 的 `-50` 不能改称新轨 writer 证据。

真实 reel 的 `clean_span_receipt_artifact_id` 必须指向 `ck3-war-ai.episode02.clean-span-audit.v1` JSON，含 `result="GREEN"`、`attempt_id`、`span_id`、`capture_artifact_root` 绝对路径、`raw_video_sha256`/`raw_video_bytes`、`report_sha256`、`timeline_sha256`、`evidence_index_sha256` 及 `begin_seconds`/`end_seconds`。composer 只读调用正式 CK3 adapter 的 `load_capture_bundle`，对精确 `span_id` 重新验证报告、timeline、索引、raw、两端 clean frame 和时段；自称 GREEN 的占位 JSON 不能代替 adapter 结果。`label_audit_artifact_id` 必须指向 `ck3-war-ai.episode02.source-label-audit.v1` JSON，含自报 `status="visible"`、相同 `attempt_id`、raw/reel SHA、含 attempt ID 的 `label_text`、处于 reel 时长内的 `frame_at_seconds`，以及已保全标记帧的 `frame_artifact_id`/`frame_sha256`/`frame_bytes`。机器只核对标签声明和标记帧的来源/字节关联，**不能证明标签确实可见**；标记帧和完整成片仍须人工观看。合成 smoke 仍使用显式 `synthetic.clean-span.v1` 与 `synthetic.source-label.v1`，不能流入真实候选。

新 run 前再次查询正式 xar-promo Release、安装所选 wheel 并核 SHA。六章素材齐全时，命令形状是：

```text
<verified-python> -m war_ai_promo.assemble_episode_two --run-manifest <NEW_RUN>/run-manifest.json --attempt-directory <NEW_EXTERNAL_ASSEMBLY_ATTEMPT> --selected-version 0.2.1 --selected-wheel-sha256 f8de0711415e7fce2bf07a34d3db4edc0593f32ba1cb61034946665e27014621
```

版本和 SHA 是 2026-09-28 本次已核值，不代表后续 run 永久使用 0.2.1。组装后的自动检查尚不涵盖整片真实画面、字幕安全区、色彩、逐帧 PTS 连续性或人工审片；这些门仍须使用独立证据和精确成片 SHA 收口。

`--synthetic-technical-smoke` 只用于合成素材技术测试。它仍走相同的来源卡、artifact SHA/长度、reel、字幕、混音和完整解码门，并额外要求 production inputs 和每条 reel receipt 显式 `synthetic=true`、每条 span 有 `SYNTHETIC-` attempt ID 和固定的非游戏存档 marker；输出状态写为 `SYNTHETIC_TECHNICAL_SMOKE`，回执列出每条合成源身份，不能充当真实画面或人工签核。公开入口脚本 `integration/scripts/smoke_episode_two_assembly.py` 只在全新外置 attempt 中生成测试视频、音频和 native run。
