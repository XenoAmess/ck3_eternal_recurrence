# 天朝二期宣传片 readiness（2026-09-02）

本文是最终宣传片的施工清单，不是 live、候选成片或发布声明。旧一期录像、fixture、静态配置、MCP snapshot
和生成边界卡都不能代替下列二期实录。

## 冻结工具与检查结论

- 父仓检查基线：`09f21c8958d9f880d4993c69ce967abc88bdb175`。
- 独立宣传工具：`Z:\workspace\xar_promo_toolchain` 的 `main == origin/main ==
  57c42fca13ea459432c1caf76e069a1fbccf602c`，工作树 clean；版本为 `0.2.1`。
- `v0.2.1` wheel：`190405` bytes，SHA-256
  `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`。父仓默认依赖已更新到该
  release；本次源码检查显式设置 `XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain`，没有调用旧版。
- 独立工具普通/优化测试各 `263` 项 GREEN。父仓 builder、producer、runner 与 seed capture focused suite 为
  `55 passed, 2 subtests passed`。
- 对当前 `phase2-promo-project.json` 的 `--validate-only` 返回 exit `2`：十章全部仍为 `planned`；入口没有创建
  workdir，也没有读取缺失 capture、调用 TTS 或媒体进程。配置 SHA-256 为
  `150EE549AF859517C377D3CD531414E9C76E133A8168AF2B0168797249B62129`。
- runner 已内置 managed-runtime producer adapter：它复用现有 paused-map 与 schema-v2 loaded-seed proof，并由默认
  composite driver 静态拥有全部 8/8 handler。`span_handlers_missing` 现在只适用于兼容 registry 或自定义 driver 回退，
  不再是默认入口的当前 blocker。八个 handler 的真实 event/GUI/MCP provider proof 仍全部保持 false，必须由同一次实机
  span 执行逐项转为 GREEN；seed 未就绪仍为 `seed_not_ready`，这些 RED 都不会产生录屏。
- `open_kaishek` 支撑主线锚点为 `17caa28`。它继续随项目演进提供离线预验，但不会把当前 loader/native RED、
  缺失 paused artifact 或缺失视频素材升级为 live。

## 八段必须来自同一次真实二期 capture

真实 producer 必须在 gameplay HUD 出现后开始录制，使用真实历史角色，按固定合同产生下列八段 clean span；
每段都要有 begin/end mark、完整原始 MKV 时间范围、fixture/test UI 缺席门与同源 bytes/SHA 绑定：

1. `phase2_fact_quota_calibration` / `facts-quota-calibration`：事实档、配额档、背靠背互评与校准债。
2. `phase2_receipt_appeal_pip` / `receipts-appeals-pip`：告身、申诉、PIP 与跨周期追踪。
3. `phase2_manager_governance` / `manager-governance`：京察拒办、团队快照、经理上级与连责。
4. `phase2_promotion_compensation` / `promotion-compensation`：晋升包预留、答辩、职级与薪酬结果。
5. `phase2_hc_workforce` / `hc-workforce`：HC、继任、流动与无编制结果。
6. `phase2_projects_metrics` / `projects-metrics`：项目、跨部门抢功、贡献份额、指标与重组。
7. `phase2_incidents_operations` / `incidents-operations`：事故、积弊、共享官署与技术债后果。
8. `phase2_cross_cycle_endgame` / `cross-cycle-endgame`：跨周期债、默认变更和制度终局。

producer gate 只等待可核验的 loader completion、同 PID managed session 与真实 paused seed，不再依赖旧的
`database_callback_stall` 文本。上述 native/paused 证据闭合前不启动同形 capture 重试。当前状态仍是
`static-ready + native-readiness RED + not-live`。

## 十章 authoring、媒体、TTS 与字幕

取得八段同源实录并确认能支持声明后，再把十章逐章从 `planned` 改为 `ready`。每章至少创作一个 globally unique cue，
每个 cue 必须同时具备：中文 narration、简中/英文同屏字幕、对应 `artifact_ids`，以及可由真实画面承载的时长。

| 章 | 画面来源 | 当前缺口 |
| --- | --- | --- |
| `phase2_minimal_recap` | 新生成开场卡 | cue、双语字幕、Xiaoxiao 音频 |
| `phase2_fact_quota_calibration` | 二期 clean span 1 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_receipt_appeal_pip` | 二期 clean span 2 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_manager_governance` | 二期 clean span 3 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_promotion_compensation` | 二期 clean span 4 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_hc_workforce` | 二期 clean span 5 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_projects_metrics` | 二期 clean span 6 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_incidents_operations` | 二期 clean span 7 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_cross_cycle_endgame` | 二期 clean span 8 | 实录、cue、双语字幕、Xiaoxiao 音频 |
| `phase2_finale` | 新生成收尾卡 | cue、双语字幕、Xiaoxiao 音频 |

旁白固定为 `zh-CN-XiaoxiaoNeural`。先以最终中文稿生成 content-addressed Edge TTS cache，再由 ffprobe 读取每条真实
音频时长；authoring estimate 不能进入 release。每条音频、ASS、生成卡、章节 MP4、原始 MKV、失败 take、命令审计与
中间导出都留在新的仓库外 attempt 目录。最终 H.264/yuv420p + AAC 48 kHz stereo 成片必须短于 `1200s`，且不得包含
Launcher、loading 或测试 UI。

## runtime claims、人审、导出与发布

1. 取得与同一 seed/source identity 绑定的 GREEN `preflight.json`、capture `report.json`、timeline、evidence index、
   raw recording、八段 clean gates、真实历史人物/头衔 provenance，以及项目专用 runtime claim matrix。
2. 运行一次普通候选构建；builder 必须使用新 workdir、离线 TTS cache、真实 ffmpeg/ffprobe，并在结束前重验所有 capture
   bytes/SHA。任何失败 attempt 原样保留，不在同一路径重试。
3. 对八段源素材逐段 1× 完整观看并抽帧/OCR，签署 fixture/test UI 缺席、仅历史角色、无裁切遮罩等项目 attestation。
4. 对最终 MP4 的精确 bytes 再做一次独立 1× 全片人审；字幕安全区、同步、首尾帧、章节边界和叙事声明全部通过后，
   由真实 reviewer 对该 deliverable SHA 记录 approved sign-off。自动测试不得代签。
5. `xar-promo export` 只在 release profile、选定 deliverable approval 与 allowlist policy 全部 GREEN 后生成本地 bundle；
   它不联网、不发布。外部视频平台上传、页面核对及发布记录仍需单独执行，未实际发生前必须写 `publish_performed=false`。

## 下一项施工

当前视频侧不再添加 fixture plumbing。managed runtime probe、默认 producer 注册、registry adapter 与固定八段 executor 已
`static-ready`；主线先闭合天朝二期 loader callback/native paused gate，并为八个 canonical handler 逐项接入真实玩法 surface。
八项齐备后同一 adapter 可直接生成八段同源 capture。capture 通过后才能根据画面写最终中文稿、英文字幕、TTS、候选成片与人审包。
