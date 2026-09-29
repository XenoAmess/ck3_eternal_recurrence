# 第二期：经审 clean span 到六条候选 reel

2026-09-29，针对 #451 的六章正式组装入口补一段可执行的**离线 reel 编辑器**：[入口](prepare_reel_edit.py)、[实现](../integration/src/war_ai_promo/episode_two_reel_edit.py)、[聚焦检查](../integration/test_episode_two_reel_edit.py)。当前没有一条实际已获 1× 原速人审和 CK3 adapter GREEN 的 clean span，故没有运行真实 `build`、没有六条 reel、没有 29:50 MP4，更没有成片人工签核。现有四 raw a03 窗、E2-05 a02 连续 PTS、稀疏帧索引和 E2-04 的新原始录制都不能直接当输入。

本轮再查独立仓库正式 GitHub Release，最新仍为 [`xar-promo-toolchain v0.2.1`](https://github.com/XenoAmess/xar_promo_toolchain/releases/tag/v0.2.1)，本机显式解释器 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` 报 `xar-promo 0.2.1`；wheel SHA-256 `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。顶层与 `plan`/`build` 帮助已核。新 run 仍须届时再查 Release；编辑器的 `build` 再核解释器安装 wheel 版本/SHA。

## 最小输入合同

`ck3-war-ai.episode02.reel-edit.v1` JSON 是**待编辑源表**，`status` 必须为 `reviewed-clean-spans-edit-planned`、`synthetic=false`、`human_signoff=not-provided`。必须显式写四件 `{source,bytes,sha256}`：当前 ProjectConfig、中文稿、六章字幕 `subtitle-input-fragments.json` 与正式九卡 `calculation-cards.json`。字幕原件须仍绑定同字节配置/中文稿；卡索引及卡 SVG 须与当前正式九卡精确身份一致。六章顺序及逐章目标帧数固定：

| chapter | `target_frames` @ 30 fps | 目标时长 | 当前 TTS 秒数 |
| --- | ---: | ---: | ---: |
| `opening` | 2700 | 1:30 | 77.808 |
| `pursuit` | 10200 | 5:40 | 253.824 |
| `knights` | 12000 | 6:40 | 328.752 |
| `reinforcement` | 15450 | 8:35 | 332.712 |
| `terminal` | 10500 | 5:50 | 269.232 |
| `closing` | 2850 | 1:35 | 88.056 |
| **合计** | **53700** | **29:50** | **22:30.384** |

每章 `segments[]` 的整数 `frames` 必须恰好加到上表，也必须至少有一条真实 capture。`pursuit` 只许含 E2-02/03 两张正式卡；`knights` 恰含 E2-04、E2-05A/B/C 四张；`reinforcement` 恰含 E2-06/07；`terminal` 恰含 E2-09；开场/收束无正式卡。卡页独读、转场和旁白期间画面都必须在这 53,700 帧内具体安排，不能靠命令默默填尾。

`kind=capture` 每段需唯一 `id`、真实 `attempt_id`、adapter `bundle_root`、`span_id`、原片 `raw_width/raw_height`、**实际帧 PTS** `begin_pts_seconds/end_pts_seconds`、`frames` 与含 attempt ID 的可见 `source_label`；还需以下每件原件的绝对路径/bytes/SHA：bundle 复制的 `raw`、`clean_span_audit`、bundle 内 `source/human-review.json`、完整 `pts_probe`、`recorder_final`、实际冷载 `cold_load_save` 与原生回执 `cold_load_receipt`、当次 `control`。帧预算要求 `|(frames−1)/30 − (end−begin)| ≤ 0.001` 秒，两端必须落在计划输出的首末帧；`10→12` 秒用 60 帧会因缺第 61 帧而拒绝。编辑器读 `clean-span-audit.v1 result=GREEN`、真人 `full_raw_1x_and_exact_span_endpoints` 记录，并实调正式 `load_capture_bundle`，核原 raw、三件套、原始端点与被选子段；完整 FFprobe 中两端必须是真正存在的帧 PTS，内部间隔不得大于 0.2 秒。冷载 pair 必须与当次 `recorder-intent.json` 相同，control 须位于该 attempt 原件清单；`source-manifest.json` 与 `recorder-intent.json` 按**初次解析的精确字节**记录路径/大小/SHA，写进 `verified-inputs.json` 及候选来源索引，编码结束后再逐字节重核。`source_label` 会作为独立 ASS 字幕烧进此段**顶部**；机器烧字不等于人工确认实际可读或没有遮住 UI。

`kind=still` 每段需唯一 `id`、`frames`、2560×1440 PNG `image`、原始 `origin` 和 `still-raster.v1` `render_receipt` 三项精确身份，及来源标签。渲染回执最少写 `schema`, `status=rasterized-unreviewed`, `image_sha256`, `source_sha256`, `width=2560`, `height=1440`，另应保存实际 SVG→PNG 渲染 argv、软件版本和 stdout/stderr。正式计算卡给 `card_id`，`origin` 必须是九卡索引旁的精确 SVG，标签包含 `card_id` 与 replay；039→040/020/070/036→038 的历史卡另须写 `历史研究`、`非当前录制`。非正式身份页可不填 `card_id`，但仍必须绑定其 `origin` 和 PNG 生成回执。卡 raster 的原件与失败尝试另存在新外置目录；编辑器不会造出未经查验的 SVG 渲染图。

同一原片 PTS 不准悄悄复用。收束章若回顾前章**未来真正准入**的原片，在 `recap_of` 指明前章 segment ID，PTS 须落在该段以内，标签另标“回顾”；不能把另一次 A01 录制称作 A05 同轨。含当前 A05/A01 正式卡的章节，其**全部** capture 段必须与该卡同 attempt、同冷载 save。E2-04/05、A01 增援、A05 追击/终局各有独立来源；一个 attempt 的 card 数字不能无标签地配另一个 attempt 镜头。

## 命令与输出状态

`check-shape` 是**纯读**的结构排期检查，不哈希 raw、不调用 adapter；结果只写 `STRUCTURE_ONLY_UNVERIFIED_ORIGINALS`。它能在稿仍缺片时提示六章、帧数、卡片、attempt 标记和重复区间问题，但不能准入素材。

```text
<verified-python> promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_reel_edit.py check-shape --spec <ABSOLUTE_REEL_EDIT_JSON>
```

待全部段落有真实 1× 人审、GREEN adapter bundle、独立 PNG 与完整时长，再从已核的解释器运行 `build`。`--attempt-directory` 必须是仓库外**从未存在**的新目录；构建前和媒体编码后分别核源字节、FFmpeg/FFprobe 实际可执行文件 SHA 与版本输出。FFmpeg 单段从原片精确 PTS 截取或从显式 PNG 静帧，结束 PTS 是最后一个**纳入**的原片帧。capture 不设 `-frames:v` 截断上限，必须编码完整的 trim 区间，再由 FFprobe 实测逐段帧数、时长、分辨率和 30fps；still 仍按显式帧数限制。输出 2560×1440/30fps 视频段，以固定 H.264 参数无音频编码，再按固定顺序 concat 为**六条互不覆盖的 reel**。每步先落 argv，再把 stdout/stderr 流式写入独立文件；正常非零、启动失败或 Python 收到 Ctrl-C 时记录退出/中断回执、保留 partial，`build` 写 `failure.json`，另开 attempt 重做。宿主机强制断电或进程被外部强杀时，Python 无法补写未执行的回执，只能保留已经落盘的过程文件。编码后再核 adapter 原件、其他声明输入与媒体工具。

```text
<verified-python> promo/ck3_native_war_ai/episode-02-battle-second-half/prepare_reel_edit.py build --spec <ABSOLUTE_REEL_EDIT_JSON> --attempt-directory <NEW_ABSOLUTE_EXTERNAL_DIR> --selected-version 0.2.1 --selected-wheel-sha256 F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621
```

成功仅产 `candidate-reels.json`，状态 `ENCODED_PENDING_HUMAN_REEL_AND_LABEL_REVIEW`；它**故意不产生** `chapter-reel.v1` 正式回执，也不创建整片。编辑器不能证明来源标签在真实输出里可见、卡片读得清、弹窗未挡关键 UI，亦不能替任何人看完六条 reel。之后真实审阅者要对每条**编码后的字节**按原速观片，抽实际 reel 标签帧、填 `source-label-audit.v1` / 历史 `card-label-audit.v1`，为正式 A05/A01 卡填同 attempt 重算回执，再创建精确 `chapter-reel.v1`。`prepare_production_inputs.py` 随后核正式六条 reel 与全部来源并生成 preserve plan；在新 native run 保全后，已有 `war_ai_promo.assemble_episode_two` 才能用 v0.2.1 `plan`/`build`、固定主题曲混音和章节探测产**一条 29:50 技术候选 MP4**。该片仍需 1× 全片真人观看并按最终 SHA 签核；此前不传 OneDrive、不写成片完成。

追加独立外置技术 smoke：`D:/workspace/ck3_native_war_ai_promo_work/episode02-reel-frame-budget-smoke-20260929-a02/`，回执 `smoke-receipt.json` SHA-256 `88CE81B39242BE79D399BCAEB2F67450241831231D381715CEADFC7B11C667A3`。64×64 合成原片 60 帧，首 PTS 0、末 PTS 1.967；不设 `-frames` 限制时，以排他结束 `1.967` 截取仅 59 帧，结束设 `1.968` 后为 60 帧、2.000 秒。源、两条 MP4、各命令 argv/stdout/stderr、完整 FFprobe JSON 均永久保留。聚焦负例另证明 100 秒源区间只给 30 帧，以及 1 秒区间给 60 帧会 RED。该 smoke 只证小样本的 FFmpeg 边界行为，**不证明**真实原片未来的编码、画面连续性、标签可读性或人工签核。真实媒体 gate 仍待取得合格素材后运行。
