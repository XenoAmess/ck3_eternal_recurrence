# 第二期六章 composer 最小入口

2026-09-28，无屏幕技术准备。项目 composer 是 `war_ai_promo.episode_two_second_half:compose`，按当前正式 [xar-promo v0.2.1](https://github.com/XenoAmess/xar_promo_toolchain/releases/latest) 的 `plan`/`build --composer MODULE:ATTRIBUTE` 合同实现；它只读取同一 native run 已保全的音频、六段 chapter reel、来源稿与三张计算卡。**现在只有编辑资产检查能 GREEN；没有六章 reel、正式配音或英文字幕，不存在可通过的成片 plan/build。** `plan` 是只读，`build` 必须用新 workdir，均不启动 CK3或发布。

## 已完成的无 run 编辑门

用本 worktree 的 `integration/src` 作 Python import 根目录，已执行：

```text
D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe -m war_ai_promo.episode_two_second_half --editorial-check --config D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\project\promo-project.json --draft D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\narration-script-draft.md --cards-dir D:\w\e2\promo\ck3_native_war_ai\episode-02-battle-second-half\cards
```

返回 `editorial-inputs-present-not-media-ready`：ProjectConfig 六章顺序正确；当次 e2 稿 SHA-256 `7F0972E042016D7D7B6B558CF54B866E139512FCE481DB6696F895D1BCAEBCA3`（`f9ef02bf4` 修正了骑士段来源说明）。此前四段 TTS 样片和时长审计绑定的是旧稿 `7352B0E4...6BFE7C`，正式配音需按新稿重新量时。计算卡目录表 SHA-256 `32A589406FE592B637D2645DD6A270C15AE1DD7CEB5E78E061AD1818A0EEB1C0`，E2-06/07/09 SVG SHA 分别为 `767543A9...D866AF5`、`91BCCA2B...0CD527`、`24EE5070...0A2E97F2`。卡的原始生成器另有 `--check --verify-sources`，其 `085` 与 `024` 必须保持两条独立回放。编辑门只读存在性、字节与来源分区，不进行视频渲染、游戏接入或 TTS。

## 真正的生产输入

先在**新** xar-promo native run 内保全六类输入，保留每一步原件、命令、probe、stdout/stderr、失败 partial 与哈希：

1. 精确 `ProjectConfig` snapshot 由 `start-run` 创建；额外保全当次正式 `narration-script-draft.md` 为 `episode02-narration-script`。录音前须按新实机轨迹校对每个数字、ID 与口读，更新稿并在新 run 冻结。composer 要求每章 `zh` 字符串与该冻结稿的**旁白段落**一致，不读脚注、画面指令或来源路径。
2. 三张独立计算卡的 `calculation-cards.json` 和 SVG，artifact IDs 为 `episode02-card-index`、`episode02-card-E2-06`、`episode02-card-E2-07`、`episode02-card-E2-09`。E2-06/07 只属于 085 增援章节；E2-09 只属于 024 终局章节。若新录制轨迹改变数字，先改卡源 JSON、重建 SVG 和旁白，再冻结**新** run。
3. 六章已测时音频 `audio.<chapter-id>`，连同原 TTS request/response/事件/版本、`ffprobe` 与字幕边界分别保全。样片时长估算不是正式六章配音；默认同声线 EdgeTTS `zh-CN-XiaoxiaoNeural/-12%`，必要改声线要记新 run。每章还要有实际英文字幕文本。
4. 经 CK3 adapter 只读验过 raw、report、timeline、evidence index、marks 和 clean spans 后，剪成六条 1× chapter reel `reel.<chapter-id>`。每条 reel 的私有 `reel-receipt.<chapter-id>` 记录精确媒体 bytes/SHA/时长、捕获 span 的 attempt/save/raw/control/clean-span 与来源卡标记审核回执。不同 attempt 的镜头只在明确可见来源卡和分隔处接合，不接作同一段连续游戏。计算卡以**全屏独立插页**放进 reinforcement/terminal reel；字幕安全区 `y=1120..1439` 不覆盖原版 UI。当前旧录像不能用来证明新回放的逐日数字。
5. 最后保全 `episode02-production-inputs-v1` JSON，schema 为 `ck3-war-ai.episode02.production-inputs.v1`、`human_signoff="not-provided"`，包括上面源稿/卡 SHA 与六章有序行。每行 `id`、`title`、`zh`、`en`、`speech_duration_seconds`、`duration_seconds`、`audio_artifact_id`、`reel_artifact_id`、`reel_receipt_artifact_id`；时长来自本 run 的音频与 reel probe，不能沿用初稿 29:50 占位码。

composer 读取上述 run artifact，重新验 SHA、章节次序、旁白全文、卡的 085/024 分区、reel bytes/时长、音频测时和来源回执字段。每章成为一个 `SegmentDraft`，2560×1440/30fps，用已保全的 reel 视频和已备的配音生成中文与英文字幕，最后合成**未混主题曲**的 `episode-02-second-half-unmixed.mp4`。主题音乐、固定增益、完整解码、字幕/色彩/PTS、人工 1× 观看与精确文件签核属于后续独立门，不能从 composer 成功推断。

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
