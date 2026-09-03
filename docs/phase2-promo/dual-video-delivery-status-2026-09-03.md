# 天朝二期双版本宣传片交付状态

本文件是两条成片的交付索引。两条片子都是正式交付物，必须分别制作、分别审片、分别导出；任何一条通过，都不能替另一条签核。

## 两条成片

| 版本 | 导演处理稿 | 项目配置 | 目标文件 | 当前状态 |
|---|---|---|---|---|
| 人物线 | [`phase2-character-director-treatment.md`](phase2-character-director-treatment.md) | [`phase2-promo-character-project.json`](../../mod_zhongguo_style/promo/phase2-promo-character-project.json) | `artifacts/demos/2026-09-03/zhongguo-361-phase2-character-led.mp4` | `authoring-ready`；真实 CK3 素材 `0/8`，未导出 |
| 制度群像线 | [`phase2-institution-director-treatment.md`](phase2-institution-director-treatment.md) | [`phase2-promo-institution-project.json`](../../mod_zhongguo_style/promo/phase2-promo-institution-project.json) | `artifacts/demos/2026-09-03/zhongguo-361-phase2-institution-led.mp4` | `authoring-ready`；真实 CK3 素材 `0/8`，未导出 |

两条片子的制作总合同、镜头顺序、审片和导出命令见 [`phase2-dual-cut-production.md`](phase2-dual-cut-production.md)。导演设计分别见上表中的两份处理稿。

## 已完成

- 两条独立的导演处理稿、项目配置、authoring claims ledger、cut ledger 和审片入口已经落盘。
- 宣传工具已在可写 fresh clone 中更新并核验到 `origin/main`：
  `57c42fca13ea459432c1caf76e069a1fbccf602c`。
- 双版本 builder、intake、preflight、materializer 和 completion gate 的静态测试已通过；测试通过不等于有成片。
- 两条目标 MP4 的命名、输出目录、SHA-256 记录和独立审片边界已经固定。

## 当前未完成与原因

目前两条目标 MP4 均不存在，原因不是脚本或导出命令缺失，而是 CK3 `1.19.0.6` 在进入 mod loader/database 前崩溃，无法产生本轮要求的 8 段 clean spans。复现与 dump 证据见 [`live-startup-blocker-2026-09-03.md`](live-startup-blocker-2026-09-03.md)。因此当前不能把旧截图、旧 fixture 或占位视频写成“最终成片”。

本次对已有一期/fixture 静帧目录做了只读 intake 复核，结果为 `RED / footage_pending`（`ck3_started=false`、`ffmpeg_started=false`、`media_generated=false`）；回执位于 `Z:\ck3_mod_rewrite\_runtime\phase2-dual-video-status-20260903\fixture-intake-red.json`，SHA-256 为 `D34CF4070C0D474A06F29BA2C3A0707E4BA391D42D5C700992A6BE826D67A2A2`。这确认旧 fixture 不能直接升级为两条二期成片。

仓库中虽然还有 2026-08-29 的 `zg361-promo-pipeline-smoke.mp4`，但它是旧版单段 smoke 产物，不满足本次二期八段 lineage、独立双剪辑和真人审片要求，因此不作为任一版本的交付文件。

## 解锁后的并行交付顺序

1. 在稳定的 CK3 桌面会话取得同一 seed 的 8 段 clean spans，并完成只读 footage intake。
2. 人物线与制度群像线并行生成各自 TTS、字幕、候选片和媒体审计包。
3. 两条线分别完成 claims audit、两位审阅者的完整 1.0× 审片、sign-off、export 和 SHA-256 receipt。
4. 将两条最终 MP4 的实际路径、时长、分辨率、编码、哈希和审阅回执回填到本索引及 `README.md`，再标记各自 `complete`。

在第 1 步真正解除前，不给出虚假的固定完成时间；一旦素材齐备，采集预计约 20–30 分钟，单条候选制作预计约 45–60 分钟，之后还需两轮真人审片。两条线可在素材 intake 完成后并行推进。
## 2026-09-03 08:00 制作 runbook 回执

人物版与制度群像版已分别生成独立制作 runbook：

- 人物版：`_runtime/phase2-dual-runbooks-20260903-0800/character-runbook.json`，`RED / footage_pending`，SHA-256 `55E2751FBC8408682B04251C3706928A2C78B9B70F61D11D3D6C829DC572E408`。
- 制度群像版：`_runtime/phase2-dual-runbooks-20260903-0800/institution-runbook.json`，`RED / footage_pending`，SHA-256 `6A3FD533B0656722CF8296224A286586F5AF8B568ECDA6C7B9B3A157007BF2BF`。

这一步只生成了可复现的制作计划，没有启动 CK3、TTS、FFmpeg，也没有导出或发布媒体。两版 authoring ledger 均已静态验证 GREEN；正式 MP4 仍等待真实 CK3 八段 clean spans。
