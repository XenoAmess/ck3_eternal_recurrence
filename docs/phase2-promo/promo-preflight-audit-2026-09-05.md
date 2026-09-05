# 天朝二期宣传工具更新与真实媒体环境回执（2026-09-05）

状态：**宣传工具更新前置已完成；媒体环境 GREEN；双片仍为 footage pending。**
本工作包不启动 CK3，不制作占位媒体，不签署真人审片，不发布；日报/周报由协调者合并。

## 更新顺序与结果

2026-09-05 10:19:53（Asia/Shanghai），先检查 `Z:\workspace\xar_promo_toolchain`
的版本、分支和 clean 状态，然后实际执行：

```powershell
git -C Z:\workspace\xar_promo_toolchain pull --ff-only origin main
git -C Z:\workspace\xar_promo_toolchain rev-parse HEAD origin/main
git -C Z:\workspace\xar_promo_toolchain status --short
git -C Z:\workspace\xar_promo_toolchain describe --tags --always
```

拉取返回 `Already up to date.`；更新前后均为 `main`、工作树 clean，
`HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`，
`describe=v0.2.1-1-g57c42fc`，源码版本 `0.2.1`。没有新提交需合并，也没有本地修改需提交。
历史 `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` 是 detached checkout，保持原样。

随后使用明确解释器和源码路径核验了实际 `python -m xar_promo --help`：十个命令仍为
`init/start-run/validate/preserve/signoff/plan/build/audit/review/export`；没有 publish 命令。
已读当前工具 `README.md` 与 `docs/architecture-and-migration.md`，不虚构新的制作入口。

## 解释器与源码覆盖

当前 secondary worktree 的相对 `tools/.venv/Scripts/python.exe` 不存在，因此显式使用并核验：

- 解释器：`Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe`，Python `3.13.2`；
- `XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain`，项目 wrapper 实际加载该 checkout 的 `src/xar_promo`；
- 源码 `xar_promo.__version__=0.2.1`；Pillow `12.3.0`，edge-tts `7.2.8`；
- **安装元数据仍为 `xar-promo-toolchain 0.1.0`，不能把它误报成已安装 0.2.1 wheel。**

本轮没有在协调者的 CK3 长局期间修改共享 venv。`XAR_PROMO_SOURCE` 由项目
`promo_toolchain_loader` 消费，不是 Python 本身的模块搜索参数；因此直接运行工具 CLI
时还应明确设置如下 `PYTHONPATH`，以保持与 wrapper 相同的最新源码：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
$env:PYTHONPATH = 'Z:\workspace\xar_promo_toolchain\src'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' -m xar_promo --help
```

共享解释器可在不影响进行中任务时按当前 `tools/requirements-promo-toolchain.txt` 升级到
hash-pinned `0.2.1` wheel；本轮 source override 的 GREEN 不依赖该升级，也不声称已经完成它。

## 人物版真实环境预检

本次没有重复旧版全量单测、authoring 校验、no-media runbook 或素材复用审计。
唯一新增的制作准备是运行现有 `preflight_phase2_media.py`，实测当前网络语音目录、字体、
字幕内存布局、FFmpeg/ffprobe 编解码能力和拟用输出路径。命令为：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' mod_zhongguo_style/tools/preflight_phase2_media.py `
  --output Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1021\media-environment-character.json `
  --project-config mod_zhongguo_style/promo/phase2-promo-character-project.json `
  --expected-toolchain-head 57c42fca13ea459432c1caf76e069a1fbccf602c `
  --planned-work-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-character-led-final-20260905 `
  --planned-tts-cache Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-tts-cache `
  --planned-export-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-character-led-export-20260905
```

运行前只创建新的 receipt 父目录，没有创建候选 workdir 或媒体。退出码 `0`，
`PHASE2 MEDIA PREFLIGHT: GREEN`。回执：

- 路径：`Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1021\media-environment-character.json`；
- SHA-256：`E441A38C24FF2CE935BC85384300015FC831196BBEF44494BF05C1C791EEDC21`；
- 生成：`2026-09-05T02:21:17+00:00`，有效至 `2026-09-06T02:21:17+00:00`；
- `fresh_fetch_verified=true`，`production_refresh_still_required=false`；
- 实际 Edge 目录包含 `zh-CN-XiaoxiaoNeural`，没有合成语音；
- FFmpeg/ffprobe `8.1.1-full_build`，`libx264`、AAC、ASS/libass、`yuv420p`、MP4 能力可用；
- 实际加载 Microsoft YaHei UI/Segoe UI，双语布局在内存安全区内；没有生成字幕媒体或测试视频；
- `ck3_started/tts_synthesis_performed/subtitle_media_written/ffmpeg_encode_started/work_directory_created/candidate_generated` 全部为 `false`。

该回执只绑定人物版 draft 配置 SHA-256
`963735C8D32725A83D4A764CFD92D3C85519500C44FB2D71823F51992DB7042F`。
制度版配置 SHA-256 为 `77537A37D2D1B3E00F38120667491F8CF7047E999DFEEF640DCB8D4343524C7E`；
**不把同一环境回执冒充制度版或未来 promoted 配置的生产回执。** 素材审阅后配置发生变化时，
仍按既有双片生产合同分别绑定新配置和真实 source bundle。

## 10:58 制度版独立环境回执

按协调者后续明确工作包，制度版另跑一次现有预检，绑定它自己的 draft 配置。
没有重跑人物版、拉取或旧单测；沿用本日 10:19 已更新的工具 HEAD 和明确源码覆盖：

```powershell
$env:XAR_PROMO_SOURCE = 'Z:\workspace\xar_promo_toolchain'
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' mod_zhongguo_style/tools/preflight_phase2_media.py `
  --output Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1058\media-environment-institution.json `
  --project-config mod_zhongguo_style/promo/phase2-promo-institution-project.json `
  --expected-toolchain-head 57c42fca13ea459432c1caf76e069a1fbccf602c `
  --planned-work-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-institution-led-final-20260905 `
  --planned-tts-cache Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-tts-cache `
  --planned-export-dir Z:\ck3_mod_rewrite_process_assets\zg361\promo\phase2-institution-led-export-20260905
```

只新建 append-only receipt 父目录，退出码 `0`，环境 `GREEN`。新回执独立于人物版：

- 路径：`Z:\ck3_mod_rewrite\_runtime\phase2-promo-preflight-20260905-1058\media-environment-institution.json`；
- SHA-256：`5601C5679FA7834DC8EB5B76421350FAB8A68DE4493DD11CC33DB76BED1633F9`；
- 配置：10 章，`3,176 B`，SHA-256 `77537A37D2D1B3E00F38120667491F8CF7047E999DFEEF640DCB8D4343524C7E`；
- 生成：`2026-09-05T02:58:09+00:00`，有效至 `2026-09-06T02:58:09+00:00`；
- 实际源码 `0.2.1`、HEAD `57c42fca13ea459432c1caf76e069a1fbccf602c`，clean，`fresh_fetch_verified=true`；
- 六项执行 attestation 全部为 `false`，无 CK3、TTS、字幕媒体、编码、候选 workdir 或候选视频。

制度版自己的 `final_promo_readiness` 仍为 `RED / waiting-for-inputs`，原因同样为
`footage_pending` 与 `publish_target_pending`。双版现在各有本日独立 **draft 环境** 回执，
不是两部成片完成，也不适用于随后 source review 提升后的不同配置字节。

## 尚未交付的部分

环境回执诚实保持 `final_promo_readiness=RED`，原因是 `footage_pending` 与
`publish_target_pending`。这不是宣传工具更新失败，也不把外部发布目标缺失升级为本地制作的
新门禁：先继续现有四 checkpoint/八段素材主线，素材和真实 source review 到齐后，两版分别
TTS、build、claims audit、真人 1× 审片、signoff、本地 export。外部上传仍需实际目标授权。

本工作包没有产出新的 source span 或 MP4，没有改变两版剧情、配置、制作合同或已有素材。
后续脚本和取材路线复用既有 [`phase2-dual-cut-production.md`](phase2-dual-cut-production.md)
及 [`final-video-source-reuse-audit-2026-09-04.md`](final-video-source-reuse-audit-2026-09-04.md)，
不为等待实机而重复生成同样的 RED runbook。

## 11:24 接入检查：4/4 恢复点不等于 8/8 可剪辑素材

本次按协调者要求检查现有 project、storyboard、shot-list 与真实 builder 接口；
只读代码/配置并计算 draft 时长，没有重跑预检、没有改 runner/文案、没有生成媒体。
这里的 `4/4` 是需要达到的 registry 输入目标，不把未提供给本工作包的 live artifact 推断为完成。

### 已接好的部分与旧文档边界

- 两版 project 各有 10 章：2 个 generated card、8 个 canonical clean span，顺序和 producer 一致；
  全部仍 `planned`，`cues=[]`、`artifact_ids=[]`，这是等待真实素材审阅的意图文件。
- 两版 overlay 各有 10 条中英字幕/中文旁白 cue，均 `release_usable=false`；
  `promote_phase2_reviewed_authoring.py` 可消费真实 GREEN intake 与各版 source review，
  写出新的 ready project 和 promotion receipt，不需要手填旧 draft。
- `zhongguo_phase2_promo_cuts.py` 已接好独立 run/artifact/output；制度版明确重排经理段，
  并分别在项目段和跨周期段之后做 2 秒的告身/经理回切，没有共享签核。
- `mod_zhongguo_style/promo/storyboard.md` 是一期约 7:12 的旧分镜，不是二期机器输入。
  `shot-list.md` 虽附有正确的二期八段 ID，但“视觉 hook 尚未注册”的文字已过时：
  当前 `run_zhongguo_acceptance.py::_ensure_phase2_promo_capture_producer` 会安装 managed producer。
  不能照旧文档改用一期 `--promo-capture`，也不能让旧分镜中的生成边界卡替代二期八段实录。
  正式叙事权威仍是两份二期导演稿与 cut overlays；`final-storyboard.json` 在真实 candidate 后由
  `materialize_phase2_post_candidate.py` 产生，现在没有必要伪造它。

### 需要实际交入的精确输入

四项 registry 必须是 schema 2、`zg361_phase2_canonical_source_checkpoint_registry`，
按下列 handler 顺序保存同一 `seed_lineage_id` 的真实 checkpoint 与 provider/UI receipt。
registry 交给 recorder 的 `--phase2-source-checkpoint-registry`，不是直接交给视频 builder。

| registry handler | 所需 source event | 后续 canonical span |
| --- | --- | --- |
| `capture_promotion_compensation` | `zg361pp.147` | `phase2_promotion_compensation` |
| `capture_projects_metrics` | `zg361cp.26` | `phase2_projects_metrics` |
| `capture_incidents_operations` | `zg361.50`，另需 `received_self_incident_checkpoint_receipt` | `phase2_incidents_operations` |
| `capture_cross_cycle_endgame` | `zg361we.356` | `phase2_cross_cycle_endgame` |

每项还需实际 checkpoint 路径/bytes/SHA、owner/player/date、source receipt 的真实
`provider_observed/ui_state_verified`、同一 lineage，且 fixture/console 均未使用；Incident
须为 played subject、notice owner 与 player 不同。以上是现有 assembler 的输入，不是新增要求。

视频侧随后需要一个真实 `<capture-root>`，包含 `report.json`、
`cell/promo/capture-timeline.json`、`evidence-index.json`、`cell/04_phase2_seed_loaded.json`，
以及 index 已绑定的 raw recording、每段 clean begin/end 全屏帧和动作后原生 evidence。
八段输入不能用四份 save 或报告替代：

| span 后缀（均为 `phase2_`） | 必须同时可见/可证的关键内容 |
| --- | --- |
| `fact_quota_calibration` | 事实/配额档、校准动作、榜单与 query revision 变化 |
| `receipt_appeal_pip` | 告身/PIP surface；同 owner/subject/cycle/case 抵达所选 response |
| `manager_governance` | 真实经理 surface 与 AI-owned case 的原生业务终态 |
| `promotion_compensation` | 晋升选择和薪酬回执，绑定同一 frozen case |
| `hc_workforce` | 同 hash checkpoint 的 A/B/C、相同 owner/subject、可见 no-opening 结果 |
| `projects_metrics` | 真实项目选择与 contribution/metrics 结果 |
| `incidents_operations` | X/Y/Z 三个 surface 依序可见，动作后 transition/closure 可证 |
| `cross_cycle_endgame` | 终局与 carried debt/default-change cycle 的同 lineage 关系 |

`zhongguo_phase2_footage_intake.py` GREEN 后，两版各缺一份真实具名
`zg361_phase2_source_review_receipt`：绑定各版 config、overlay、intake bytes/SHA，完整
1× 播放、同 cut、顺序完整的 approved cue IDs。随后才生成 promoted project，分别重新
绑定该 project 的 24 小时 media receipt；本日上午两份 draft receipt 不能冒用。
完整 build 还需要内容寻址 TTS cache，以及与 capture source/tree 相容的 GREEN
`--seed-preflight-report`。candidate 后的 probe、audit、两轮真人 review、signoff、
export manifest 都由既有后处理链产生；当前不填假路径或假 approval。

### 正式录制前需要处理的真实接入差距

1. **clean 区间与旁白/动作画面尚未对齐。** 当前 producer 默认 `hold_seconds=2.5`；
   `run_phase2_capture_choreography` 在业务动作和 postcondition 检查以后才调用
   `recorder.clean_hold`，后者只把最终 clean hold 包在 begin/end marks 内。
   因此原始长录像里即使录到了动作，最终 clean span 也未必包含它。不能假定 8/8
   业务 GREEN 就已满足上述多个前后画面的 claims。
2. **当前没有足够的逐段时长预算。** builder 在 `build_phase2_promo_video.py` 中明确拒绝
   `chapter narration duration > clean span duration`。2.5 秒是 hold 参数，不是实际
   span 精确时长（还包括终帧检查开销）；本轮没有 live timeline，故不宣称必然 RED。
   但当前两版八条 gameplay cue 的 draft 估算约为 7.705–11.038 秒，不能依赖检查开销
   偶然把镜头拖长。最终录制须按较长一版的旁白与可见动作需求规划完整 clean 范围。
3. **短 cue 与长导演目标不一致。** 按 builder 已有 `_draft_duration` 公式
   `max(2.5, 0.8 + 非空白字符数 / 4.2)`，人物版 10 条共 `94.190 s`，制度版
   `92.524 s`，后者另有 4 秒回切；这不是 TTS 实测，更不是 8–12 分钟成片。
   两份导演稿目标分别约 9:30 / 9:40。正式叙事需在取材前后明确扩写/增加合法镜头停留，
   或诚实收窄时长目标；不能现在就把 10 条短摘要宣称为完整长片脚本。

这些是实际 producer/builder/authoring 路径之间的接入差距，不是安全审计或新门禁。
本检查只报告，没有擅自改变游戏动作、旁白、镜头长度或既有证据合同。

### 可以立即做与素材到齐后的用时

无需 CK3/媒体即可继续：补一份明确区分一期旧分镜与二期权威的当前 shot-list；按两版
较长 cue 制定每段“起始画面 → 动作 → 结果 → 可读停留”的拍摄预算；将上面精确输入作为
主线交接清单；在不预写实机结论的前提下对齐导演时长与 draft 旁白。现有 IDs、命令链、
review 模板和 run 身份已齐，不需要再造一套工具或重复生成缺素材 runbook。

从**真正可剪辑且已 intake GREEN 的 8/8**起算，若旁白/镜头时长已对齐、两版并行、
所需具名审阅者即时可用且没有返工，计划估算如下（不是本机实测吞吐）：

- source review、旁白收口与 promoted 配置：约 `15–30` 分钟；
- 两版 TTS/字幕/候选构建并行：沿用既有 `45–90` 分钟估计，不把两条简单相加；
- 各版 probe/claims audit、两轮 1× 审阅与本地 export：约 `30–60` 分钟；
- 总墙钟约 `1.5–3 小时`。两条 8–12 分钟目标片的两轮完整观看合计至少
  `32–48` 人分钟，还不含批注或返工；审阅者不足、编码争用或素材需补拍时应延长。

该估计不从当前 registry 状态起算，不包含缺失镜头补拍、实机故障修复或等待人工的未知时间。
外部上传目标与平台处理也不计入本地导出工期；没有真实发布回执时，不把本地 export 写成
现有 completion gate 所定义的 `COMPLETE`。
