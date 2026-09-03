# 天朝二期双片：录制命令卡与缺口清单（2026-09-03）

本卡是给下一位实际操作员的可复制入口。它只把已经存在的工具、脚本、双版配置和真实素材门槛串起来；本次整理没有启动 CK3，没有调用 TTS/FFmpeg，也没有生成或发布任何视频。尖括号中的值必须由新的、真实的运行产物替换，不能用 fixture、旧版 smoke 片或占位文件代替。

## 当前结论

- 宣传工具 fresh checkout：`Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903`。
- 已核对 `HEAD == origin/main == 57c42fca13ea459432c1caf76e069a1fbccf602c`，工作树干净。
- 在该 checkout 下复跑完整工具测试：`263` 项通过、`2` 项跳过。
- 双版交付队列报告：`Z:\ck3_mod_rewrite\_root-promo-split-20260902\_runtime\promo-inventory-20260903\delivery-queue-20260903-1236.json`，SHA-256 `4C7369DFBA31BF407EB42C8B3D46963E42153691D1BBCC4615F17B60FC129723`。
- 队列当前为 `RED / BLOCKED`，共享真实素材 `0/8`；下一步是 `capture_eight_clean_spans`。
- 当前执行权威 runbook 是 `_runtime/phase2-dual-runbooks-20260903-0800/character-runbook.json`
  （SHA-256 `55E2751FBC8408682B04251C3706928A2C78B9B70F61D11D3D6C829DC572E408`）和
  `_runtime/phase2-dual-runbooks-20260903-0800/institution-runbook.json`
  （SHA-256 `6A3FD533B0656722CF8296224A286586F5AF8B568ECDA6C7B9B3A157007BF2BF`）；两者均为
  `RED / footage_pending`。下面 `promo-inventory-20260903` 中的两个 runbook SHA 是较早的
  planner 输出，仅作历史回执保留，不得与当前 runbook、素材 intake 或后续 receipt 混用。
- 当前 fixture intake 只有旧 fixture 截图，缺少 `cell/promo/capture-timeline.json` 和 `cell/04_phase2_seed_loaded.json`，所以不能升级成二期素材。
- 当前没有二期 MP4、TTS 音频、候选片或发布回执。两版必须各自完成审阅、导出和哈希绑定。

## 双版输入与交付身份

| cut | 导演稿 | 项目配置 | authoring ledger | 当前 runbook | 目标交付物 |
|---|---|---|---|---|---|
| `character-led` | `docs/phase2-promo/phase2-character-director-treatment.md` | `mod_zhongguo_style/promo/phase2-promo-character-project.json` | `mod_zhongguo_style/promo/phase2-authoring-character-claims.json` | `_runtime/phase2-dual-runbooks-20260903-0800/character-runbook.json`（`RED / footage_pending`，SHA-256 `55E2751FBC8408682B04251C3706928A2C78B9B70F61D11D3D6C829DC572E408`） | `zhongguo-361-phase2-character-led-video` → `deliverable/zhongguo-361-phase2-character-led.mp4` |
| `institution-led` | `docs/phase2-promo/phase2-institution-director-treatment.md` | `mod_zhongguo_style/promo/phase2-promo-institution-project.json` | `mod_zhongguo_style/promo/phase2-authoring-institution-claims.json` | `_runtime/phase2-dual-runbooks-20260903-0800/institution-runbook.json`（`RED / footage_pending`，SHA-256 `6A3FD533B0656722CF8296224A286586F5AF8B568ECDA6C7B9B3A157007BF2BF`） | `zhongguo-361-phase2-institution-led-video` → `deliverable/zhongguo-361-phase2-institution-led.mp4` |

两版共用同一套、按固定顺序取得的八段真实 source span：

1. `phase2_fact_quota_calibration`
2. `phase2_receipt_appeal_pip`
3. `phase2_manager_governance`
4. `phase2_promotion_compensation`
5. `phase2_hc_workforce`
6. `phase2_projects_metrics`
7. `phase2_incidents_operations`
8. `phase2_cross_cycle_endgame`

共用的是通过 intake 后的原始字节、timeline、evidence index 和 lineage；旁白、字幕、剪辑项目、候选片、人工审阅和导出仍然完全独立。

## 尚未闭合的门

| 门 | 当前证据 | 关闭条件 |
|---|---|---|
| `footage_pending` | 队列 `0/8`；fixture 缺少 timeline/loaded-seed-v2 | 在真实 CK3 会话取得八段 clean span，并产生 `report.json`、`cell/promo/capture-timeline.json`、`evidence-index.json`、`cell/04_phase2_seed_loaded.json`，四者均由同一 intake 索引且哈希一致 |
| canonical seed | 已发现的 phase2 seed contract 都是 `blocked_seed_generation_required`，且仍指向被禁止的旧 save SHA | 新建 `status=ready`、`ready=true` 的非旧版 seed contract，并绑定 exact game/EXE/source/mount lineage |
| completion observer | 目前只有研究/诊断或失败运行记录，没有可供 capture plan 接受的非 fixture `GREEN` observer artifact | 生成真实、非 fixture、结果为 `GREEN` 的 completion observer receipt |
| source checkpoint registry | 代码要求 `zg361_phase2_canonical_source_checkpoint_registry`，当前没有真实 registry | 在同一次真实 seed/capture lineage 中为需要恢复的 span 生成完整 registry，并以 `--phase2-source-checkpoint-registry` 传入 |
| bridge pair | 观察到的候选文件位于 `Z:\ck3_mod_rewrite\_runtime\bridge-fresh-release-freeze165b-20260903`，但仍需和冻结的游戏/源树绑定 | 由当前 exact build 的 `xar_ck3_bridge.dll` 与 `xar_ck3_bridge_injector.exe` 组成一对，并通过实际 preflight 验证 |
| media preflight | 当前没有与本次真实 capture 绑定的 GREEN receipt | capture 和 source review 后，以工具 HEAD `57c42fca...` 重新生成 receipt，并保存其 SHA-256 |
| source review | 两个 cut 各自的 1.0x source review receipt 尚未写入 | 指定审阅者看完八段原始素材，按各自 checklist 签署、绑定 clip bytes/lineage/claims disposition |
| TTS/candidate | 两个 cut 的 Xiaoxiao cache、候选片和完整媒体审计均不存在 | media receipt GREEN 后分别 prime cache、validate-only，再各自 build candidate |
| final review/export/publish | 两轮人工审阅、sign-off、export manifest、发布目标和远端回执均缺失 | 每个 cut 独立完成两轮全长 1.0x 审阅、sign-off、导出、SHA-256 和授权发布回执 |

## 录制前只读检查（现在可以运行）

下面命令只读检查宣传工具版本和工作树，不拉取、不修改工具 checkout，也不会启动 CK3：

```powershell
$ZgPromo = 'Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903'
$ZgToolHead = (& git -c "safe.directory=$ZgPromo" -C $ZgPromo rev-parse HEAD).Trim()
$ZgToolOrigin = (& git -c "safe.directory=$ZgPromo" -C $ZgPromo rev-parse origin/main).Trim()
$ZgToolDirty = (& git -c "safe.directory=$ZgPromo" -C $ZgPromo status --porcelain)
if ($ZgToolDirty) { throw 'promo tool checkout is dirty' }
if ($ZgToolHead -ne $ZgToolOrigin) { throw 'promo tool HEAD != origin/main' }
if ($ZgToolHead -ne '57c42fca13ea459432c1caf76e069a1fbccf602c') {
    throw 'the recorded production tool receipt must be refreshed before use'
}

$env:XAR_PROMO_SOURCE = $ZgPromo
$ZgPython = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
& $ZgPython -m unittest discover `
  -s (Join-Path $ZgPromo 'tests') -q
```

这次实际复跑结果是 `Ran 263 tests ... OK (skipped=2)`。如果远端主线在正式 TTS/渲染前发生新提交，必须重新完成“更新 → 核对 → 测试 → 绑定 receipt”这一整步，不能沿用旧 HEAD。

## 先做无启动 capture plan（不会启动 CK3）

将下面变量替换为真实、已验证的输入后，先运行**不带 `--execute`** 的计划命令。它只写一个新的 `capture-plan.json`；任何缺口都会保持 `RED`，并返回非零码。`<...>` 不能原样执行。

```powershell
$ZgRepo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$ZgPython = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$ZgAttemptStamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$ZgAttempt = "Z:\ck3_mod_rewrite\_runtime\phase2-promo-capture-$ZgAttemptStamp"
$ZgSourceCommit = '<FROZEN_40_HEX_SOURCE_COMMIT>'
$ZgObserver = '<GREEN_COMPLETION_OBSERVER_JSON>'
$ZgSeed = '<GREEN_READY_SEED_CONTRACT_JSON>'
$ZgMedia = '<GREEN_MEDIA_PREFLIGHT_JSON>'
$ZgMediaSha = '<SHA256_OF_GREEN_MEDIA_PREFLIGHT_JSON>'
$ZgBridgeDir = 'Z:\ck3_mod_rewrite\_runtime\bridge-fresh-release-freeze165b-20260903'
$ZgBridgeDll = "$ZgBridgeDir\xar_ck3_bridge.dll"
$ZgBridgeInjector = "$ZgBridgeDir\xar_ck3_bridge_injector.exe"

& $ZgPython "$ZgRepo\tools\run_zhongguo_phase2_capture_attempt.py" `
  --attempt-dir $ZgAttempt `
  --source-root $ZgRepo `
  --source-git-commit $ZgSourceCommit `
  --observer-artifact $ZgObserver `
  --seed-contract $ZgSeed `
  --media-preflight-report $ZgMedia `
  --expected-media-preflight-sha256 $ZgMediaSha `
  --bridge-dll $ZgBridgeDll `
  --bridge-injector $ZgBridgeInjector
```

这个 wrapper 的 `--execute` 是唯一的 CK3 启动边界。当前 runner 的 Phase2 producer 还要求 source checkpoint registry；因此计划变为 GREEN 后，实际启动命令应显式补上该 registry，而不能只照抄一个缺 registry 的旧 `single_capture_command`。

## 实际八段录制命令（仅在所有门为 GREEN 后执行）

以下命令会启动 CK3，当前整理阶段**没有执行**。操作员必须先确认上面的 plan 为 `GREEN / ready-to-run`，并核对 `$ZgSourceRegistry` 是同一真实 lineage 的 registry。保留默认 userdir，不要加 `--discard-userdir`，以便保存失败证据。

```powershell
$ZgRepo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$ZgPython = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$ZgAttempt = '<THE_NEW_GREEN_CAPTURE_ATTEMPT_DIR>'
$ZgCaptureOut = "$ZgAttempt\capture"
$ZgSeed = '<GREEN_READY_SEED_CONTRACT_JSON>'
$ZgSourceRegistry = '<GREEN_SOURCE_CHECKPOINT_REGISTRY_JSON>'
$ZgBridgeDll = '<EXACT_BUILD_xar_ck3_bridge.dll>'
$ZgBridgeInjector = '<EXACT_BUILD_xar_ck3_bridge_injector.exe>'
$ZgBridgePipe = "\\.\pipe\xar_ck3_bridge_zg361_phase2_capture_$([guid]::NewGuid().ToString('N'))"

# EXECUTION BOUNDARY: this line starts CK3 and the recorder.
& $ZgPython "$ZgRepo\tools\run_zhongguo_acceptance.py" `
  --phase2-promo-capture `
  --artifacts-dir $ZgCaptureOut `
  --phase2-seed-contract $ZgSeed `
  --phase2-source-checkpoint-registry $ZgSourceRegistry `
  --bridge-dll $ZgBridgeDll `
  --bridge-injector $ZgBridgeInjector `
  --bridge-pipe $ZgBridgePipe
```

录制返回后，只有当 `$ZgCaptureOut\report.json`、`$ZgCaptureOut\cell\promo\capture-timeline.json`、`$ZgCaptureOut\evidence-index.json` 和 `$ZgCaptureOut\cell\04_phase2_seed_loaded.json` 都存在且内容为真实 `GREEN` 时，才继续 intake。否则保留失败目录，换新的 attempt 目录重试，不覆盖旧证据。

## 录制完成后的入库与双片并行链

### 1. 只读 intake（共享一次，不能用 fixture）

```powershell
$ZgRepo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$ZgPython = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$ZgCapture = '<GREEN_CAPTURE_ROOT>'
$ZgIntake = '<NEW_INTAKE_REPORT_JSON>'

& $ZgPython "$ZgRepo\tools\zhongguo_phase2_footage_intake.py" `
  --capture-root $ZgCapture --output $ZgIntake
```

`GREEN` intake 必须报告八个 canonical span、同一 seed/save lineage、真实 CK3 source/game/mount、raw recording hash 和全量 clean begin/end。`RED / footage_pending` 不能进入 builder。

### 2. 两版分别 source review、promote、media preflight、TTS 和 candidate

以下两个分支可以在同一份 `GREEN` intake 后并行，但每个 cut 必须使用自己的 authoring/work/run/output 路径。先由指定审阅者把真实签署的 `$ZgSourceReview` 写好，再运行 promotion；命令不会替代人工审阅。

```powershell
$ZgRepo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$ZgPython = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$env:XAR_PROMO_SOURCE = 'Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903'
$ZgCapture = '<GREEN_CAPTURE_ROOT>'
$ZgIntake = '<GREEN_INTAKE_REPORT_JSON>'
$ZgToolHead = '57c42fca13ea459432c1caf76e069a1fbccf602c'

# Character line (use a new, empty work root)
$ZgCharRoot = '<NEW_CHARACTER_AUTHORING_ROOT>'
$ZgCharProject = "$ZgCharRoot\phase2-promo-character-project.json"
$ZgCharMedia = "$ZgCharRoot\media-preflight.json"
$ZgCharMediaSha = '<CHARACTER_MEDIA_PREFLIGHT_SHA256>'
$ZgCharTts = '<NEW_CHARACTER_TTS_CACHE>'
$ZgCharWork = '<NEW_CHARACTER_WORK_DIR>'

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\promote_phase2_reviewed_authoring.py" `
  --project-config "$ZgRepo\mod_zhongguo_style\promo\phase2-promo-character-project.json" `
  --authoring-ledger "$ZgRepo\mod_zhongguo_style\promo\phase2-authoring-character-claims.json" `
  --footage-intake-report $ZgIntake `
  --source-review-receipt "$ZgCharRoot\source-review-receipt.json" `
  --output-project $ZgCharProject `
  --output-receipt "$ZgCharRoot\authoring-promotion-receipt.json"

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\preflight_phase2_media.py" `
  --output $ZgCharMedia `
  --project-config $ZgCharProject `
  --expected-toolchain-head $ZgToolHead `
  --capture-root $ZgCapture `
  --planned-work-dir $ZgCharWork `
  --planned-tts-cache $ZgCharTts `
  --planned-export-dir '<NEW_CHARACTER_EXPORT_DIR>'
$ZgCharMediaSha = (Get-FileHash -Algorithm SHA256 $ZgCharMedia).Hash

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\prime_phase2_tts_cache.py" `
  --cut character-led --project-config $ZgCharProject `
  --media-preflight-report $ZgCharMedia `
  --expected-media-preflight-sha256 $ZgCharMediaSha `
  --tts-cache $ZgCharTts `
  --output "$ZgCharRoot\tts-cache-prime-receipt.json" `
  --ffmpeg ffmpeg --ffprobe ffprobe

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut character-led --project-config $ZgCharProject `
  --capture-root $ZgCapture --seed-preflight-report '<GREEN_SEED_PREFLIGHT_JSON>' `
  --media-preflight-report $ZgCharMedia `
  --expected-media-preflight-sha256 $ZgCharMediaSha `
  --work-dir $ZgCharWork --tts-cache $ZgCharTts `
  --ffmpeg ffmpeg --ffprobe ffprobe `
  --run-id phase2-character-led-candidate --validate-only

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut character-led --project-config $ZgCharProject `
  --capture-root $ZgCapture --seed-preflight-report '<GREEN_SEED_PREFLIGHT_JSON>' `
  --media-preflight-report $ZgCharMedia `
  --expected-media-preflight-sha256 $ZgCharMediaSha `
  --work-dir $ZgCharWork --tts-cache $ZgCharTts `
  --ffmpeg ffmpeg --ffprobe ffprobe `
  --run-id phase2-character-led-candidate
```

Institution line uses the identical sequence with its own values:

```powershell
$ZgInstRoot = '<NEW_INSTITUTION_AUTHORING_ROOT>'
$ZgInstProject = "$ZgInstRoot\phase2-promo-institution-project.json"
$ZgInstMedia = "$ZgInstRoot\media-preflight.json"
$ZgInstMediaSha = '<INSTITUTION_MEDIA_PREFLIGHT_SHA256>'
$ZgInstTts = '<NEW_INSTITUTION_TTS_CACHE>'
$ZgInstWork = '<NEW_INSTITUTION_WORK_DIR>'

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\promote_phase2_reviewed_authoring.py" `
  --project-config "$ZgRepo\mod_zhongguo_style\promo\phase2-promo-institution-project.json" `
  --authoring-ledger "$ZgRepo\mod_zhongguo_style\promo\phase2-authoring-institution-claims.json" `
  --footage-intake-report $ZgIntake `
  --source-review-receipt "$ZgInstRoot\source-review-receipt.json" `
  --output-project $ZgInstProject `
  --output-receipt "$ZgInstRoot\authoring-promotion-receipt.json"

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\preflight_phase2_media.py" `
  --output $ZgInstMedia --project-config $ZgInstProject `
  --expected-toolchain-head $ZgToolHead --capture-root $ZgCapture `
  --planned-work-dir $ZgInstWork --planned-tts-cache $ZgInstTts `
  --planned-export-dir '<NEW_INSTITUTION_EXPORT_DIR>'
$ZgInstMediaSha = (Get-FileHash -Algorithm SHA256 $ZgInstMedia).Hash

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\prime_phase2_tts_cache.py" `
  --cut institution-led --project-config $ZgInstProject `
  --media-preflight-report $ZgInstMedia `
  --expected-media-preflight-sha256 $ZgInstMediaSha `
  --tts-cache $ZgInstTts `
  --output "$ZgInstRoot\tts-cache-prime-receipt.json" `
  --ffmpeg ffmpeg --ffprobe ffprobe

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut institution-led --project-config $ZgInstProject `
  --capture-root $ZgCapture --seed-preflight-report '<GREEN_SEED_PREFLIGHT_JSON>' `
  --media-preflight-report $ZgInstMedia `
  --expected-media-preflight-sha256 $ZgInstMediaSha `
  --work-dir $ZgInstWork --tts-cache $ZgInstTts `
  --ffmpeg ffmpeg --ffprobe ffprobe `
  --run-id phase2-institution-led-candidate --validate-only

& $ZgPython "$ZgRepo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut institution-led --project-config $ZgInstProject `
  --capture-root $ZgCapture --seed-preflight-report '<GREEN_SEED_PREFLIGHT_JSON>' `
  --media-preflight-report $ZgInstMedia `
  --expected-media-preflight-sha256 $ZgInstMediaSha `
  --work-dir $ZgInstWork --tts-cache $ZgInstTts `
  --ffmpeg ffmpeg --ffprobe ffprobe `
  --run-id phase2-institution-led-candidate
```

候选 build 不是 release approval。每个 cut 随后还要独立执行 materializer、`xar_promo audit`、两轮全长 1.0x 人工 review、sign-off、`xar_promo validate/export` 和授权发布回执；任意一步失败都保留该 cut 的 RED attempt，不借另一版的结果开绿灯。

## 预计时间（非承诺）

- 工具版本门：已完成；如果主线有新提交，需重新核对并绑定 receipt。
- 八段真实 capture + intake：在稳定、可用的 CK3 正式桌面会话已经准备好的前提下，当前队列估计 `20–40` 分钟；这不是从当前故障状态起算的固定 ETA。
- 素材 GREEN 后，两条 cut 的候选制作可并行，队列估计每条 `45–90` 分钟；另需 source review、claims audit、两轮人工审片和导出时间。
- 当前 `0/8` 素材、seed、observer、source registry 和发布授权均未闭合，因此不能给出“今天几点看到成片”的承诺。

## 本次静态核验

在不启动 CK3 的前提下，本轮相关测试共 `50/50` 通过：queue `4/4`、footage intake `12/12`、双 cut completion `9/9`、authoring ledger `12/12`、media preflight `5/5`、authoring promotion `3/3`、runbook planner `5/5`；fresh promo-tool checkout 另有 `263 passed, 2 skipped`。`git diff --check` 和 Python 编译检查也通过。media preflight 测试使用 `XAR_PROMO_SOURCE=Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903`，避免误读未安装的全局包。
