# 天朝二期双视频素材审计（2026-09-03）

本审计只检查文件和生成器，不启动 CK3、不调用 FFmpeg、不生成视频。

## 当前结论

- 两条成片路线均已具备独立导演稿、项目配置和 authoring claims ledger；两份 ledger 静态校验均为 `GREEN`，各有 10 个章节，其中 8 个 gameplay cue 仍等待真实 CK3 clean span。
- 当前仓库没有二期真实成片，也没有可直接替代真实素材的 8 段录屏。已有 `promo/imported/fixture-live-zga-20260829-061314-ea5f04ad` 只有旧 fixture 的 6 张画面；严格 intake 为 `RED / footage_pending`，缺少 `cell/promo/capture-timeline.json` 和 `cell/04_phase2_seed_loaded.json`，不能冒充成片素材。
- 能立即交付的部分是：两个独立 runbook、素材缺口报告、TTS/字幕/候选视频的执行命令模板。TTS 和渲染必须等 8 段真实素材及对应媒体 preflight 后才能开始。

## 已生成证据

| 项目 | 路径 | 结果 |
|---|---|---|
| character-led runbook | `_runtime/promo-inventory-20260903/character-runbook.json` | `RED / footage_pending`，SHA-256 `AD411E9A4F8C0A73CCDB71D4B836E8D9638AC3316914BDF417FF757D6D094E03` |
| institution-led runbook | `_runtime/promo-inventory-20260903/institution-runbook.json` | `RED / footage_pending`，SHA-256 `8A560980CE249E99B50C3E29AD0E219226C0296F51B66CFCB6F12B2BFBCC156F` |
| fixture intake | `_runtime/promo-audit-footage-20260903.json` | `RED / footage_pending`，SHA-256 `D34CF4070C0D474A06F29BA2C3A0707E4BA391D42D5C700992A6BE826D67A2A2` |

## 解锁后的精确顺序和时间

1. 在已验证的 CK3 正式桌面会话中取得同一 seed/save lineage 的 8 段 clean span，并做 intake：预计录制与整理约 20–40 分钟；这是当前唯一硬阻塞。
2. 每条路线分别做 source review、fresh promo-tool preflight、Xiaoxiao TTS、双语字幕和候选渲染：素材齐备后每条约 45–90 分钟，可两条并行。
3. 每条路线分别完成 claims audit、两轮完整 1x 人工审片、sign-off 和本地 export；至少再预留两轮审片时间。未获得真实素材前不提供固定成片时间点。

生成器入口（仅在素材 intake GREEN 后运行）：

```powershell
py tools/zhongguo_phase2_footage_intake.py --capture-root <GREEN_CAPTURE_ROOT> --output <INTAKE_REPORT>
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py --ledger mod_zhongguo_style/promo/phase2-authoring-character-claims.json --validate-only
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py --ledger mod_zhongguo_style/promo/phase2-authoring-institution-claims.json --validate-only
py mod_zhongguo_style/tools/build_phase2_promo_video.py --cut character-led --project-config <PROMOTED_CHARACTER_CONFIG> --capture-root <GREEN_CAPTURE_ROOT> --seed-preflight-report <SEED_PREFLIGHT> --media-preflight-report <MEDIA_PREFLIGHT> --expected-media-preflight-sha256 <MEDIA_SHA> --work-dir <CHARACTER_WORK> --tts-cache <CHARACTER_TTS_CACHE> --ffmpeg ffmpeg --ffprobe ffprobe --run-id phase2-character-led-candidate
py mod_zhongguo_style/tools/build_phase2_promo_video.py --cut institution-led --project-config <PROMOTED_INSTITUTION_CONFIG> --capture-root <GREEN_CAPTURE_ROOT> --seed-preflight-report <SEED_PREFLIGHT> --media-preflight-report <MEDIA_PREFLIGHT> --expected-media-preflight-sha256 <MEDIA_SHA> --work-dir <INSTITUTION_WORK> --tts-cache <INSTITUTION_TTS_CACHE> --ffmpeg ffmpeg --ffprobe ffprobe --run-id phase2-institution-led-candidate
```

以上命令不会绕过真实素材、seed lineage、媒体收据或人工审片门禁。
