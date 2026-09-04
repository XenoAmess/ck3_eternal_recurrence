# 天朝二期最终宣传片：非 CK3 准备审计（2026-09-04）

冻结基线：`ce458af71a2a44decc085766720082a8b724edb8`。

本轮没有启动 CK3、TTS、FFmpeg 或任何媒体生成，也没有对宣传工具执行 fetch、pull 或 merge。正式制作的第一步仍必须是 fresh
fetch/fast-forward，并重新证明宣传工具工作树 clean 且 `HEAD == origin/main`；本轮看到的本地 remote-tracking ref 不能代替该回执。

## 结论

- 可通过 `zhongguo_phase2_footage_intake.py` 的 Phase2 真实素材仍为 **`0/8`**。
- 已检查的项目 runtime、process-assets 与 workspace 中没有真实
  `zg361_phase2_source_checkpoint_capture_manifest`，也没有可消费的四项 source-checkpoint registry。
- 两个目标文件均不存在：
  `zhongguo-361-phase2-character-led.mp4` 与
  `zhongguo-361-phase2-institution-led.mp4`。
- 本地宣传工具 checkout 在不联网的只读观察中为 clean，且 HEAD 与本地 `origin/main` ref 都是
  `57c42fca13ea459432c1caf76e069a1fbccf602c`；因为本轮没有 fresh fetch，这不是正式制作回执。
- 现存 media-preflight/runbook 都是历史 RED 或已过期输入；未找到真实 completion attestation、两轮 1.0× review
  receipt、publish-target authority 或 publication receipt。
- 现有 Phase1 录像、pipeline smoke、fixture、no-launch candidate、静态测试、动作 ACK，以及 B2 focused
  `production-live primitive` 都不是八段 clean footage，不能计入 `0/8`。
- 两套导演稿、项目配置、双语 authoring ledger、intake/build/materialize/completion 工具已经存在；两套项目仍全部为
  `planned`，10/10 cue 均为 `release_usable=false`，必须等真实素材经过具名 source review 后才能 promote。

## 八段真实 span 与 checkpoint 合同

每个 span 都必须有同一 canonical seed/save lineage 下的真实录屏、`clean_begin/clean_end`、两张 hash-bound clean-frame
证据、provider-observed postcondition、pre/action/post revision chain、start/end checkpoint，以及独立 cleanup 回执。跨 span
允许干净重启 CK3，但单个 span 内不得换 session/PID/generation，且八段必须保持相同 source commit/tree、CK3
`1.19.0.6`/EXE、product-only mount tree 与 canonical seed hash。

| 顺序 | span | source → clean-hold surface | 额外 checkpoint / 真实缺口 |
|---:|---|---|---|
| 1 | `phase2_fact_quota_calibration` | event-free paused map → `named_widget:zg361_scoreboard_modal` | 须同时看见 identity-ready `zg361.1`，并证明 scoreboard provider revision 与 semantic fingerprint 在 action 后变化；当前没有合规 footage。 |
| 2 | `phase2_receipt_appeal_pip` | `zg361b2.40` → `zg361.4` | 同一 owner/subject/cycle/case 必须抵达所选 PIP response。B2 focused live primitive 不含本 span 的完整录像、clean gates 与 intake envelope，不能复用为 footage。 |
| 3 | `phase2_manager_governance` | event-free paused map → `zg361mg.120` | 须等待并验证 `.120` 的真实可见终态。当前只有 `GREEN_NO_LAUNCH / static-ready-live-pending` 候选，缺 paused provider artifact 与 footage。 |
| 4 | `phase2_promotion_compensation` | registry `zg361pp.147` → `zg361comp.1` | 四项 source registry 的第 1 项；checkpoint/receipt 必须绑定 played owner、保存的 subject/cycle/case、三选项与同一 lineage。provider/shared wiring 已 static-ready、默认不广告，尚无 paused live 查询与 footage。 |
| 5 | `phase2_hc_workforce` | `zg361we.360` → `zg361we.361` | Route A/B/C 必须从 hash-identical pre-action checkpoint 分叉并绑定同一 owner/subject/cycle/case；B4/B6 plumbing/provider 仍 live-pending，没有 branch archive/replay 与合规 footage。 |
| 6 | `phase2_projects_metrics` | registry `zg361cp.26` → `zg361p3.229` | 四项 source registry 的第 2 项；当前 private/default-OFF provider 只有 no-launch candidate，缺 played subject + distinct bounded AI project owner 的 paused save、live provider read 与 footage。 |
| 7 | `phase2_incidents_operations` | registry `zg361.50` → `zg361ip.190` → `.290` → `.390` | 四项 source registry 的第 3 项。`ce458af` 的当前权威身份是：player 为收件人/event root，notice/case owner 为不同角色，即 **`owner_character_id != player_character_id`**。每次 close 要证明 instance transition；当前只有 static seam，无真实 checkpoint/receipt/footage。 |
| 8 | `phase2_cross_cycle_endgame` | registry `zg361we.356` → `zg361we.361` | 四项 source registry 的第 4 项；另须 owner-side `.361` result checkpoint/restore、受控 owner→subject transition，以及同 lineage 的 subject-side Workforce provider 对 debt/charter/default-cycle 的证明。当前 seam 为 static-ready-live-pending。 |

其中 Promotion、Projects、Incident、Endgame 四项必须按上述固定顺序写入
`zg361_phase2_canonical_source_checkpoint_registry`。registry assembler 只冻结已存在的真实 bytes/receipt：

```powershell
& $Python "$Repo\tools\zhongguo_phase2_source_checkpoint_registry.py" `
  --capture-manifest $SourceCheckpointCaptureManifest `
  --checkpoint-root $SourceCheckpointArchive `
  --output $SourceCheckpointRegistry
```

它不会生成事件、checkpoint 或 provider/UI receipt。缺任一真实输入时必须保持 RED。

## 一个可入库 capture bundle 的最低结构

`zhongguo_phase2_footage_intake.py` 必须在同一 capture root 找到并逐字节核对：

- `report.json`；
- `cell/promo/capture-timeline.json`；
- `evidence-index.json`；
- `cell/04_phase2_seed_loaded.json`；
- timeline 指向且被 evidence index 绑定的非空真实 raw recording；
- `recording_started_after_gameplay_hud`、八组严格有序的 `*_clean_begin/*_clean_end`、
  `recording_stop_requested`；
- 八组 GREEN clean-frame gate，每组 begin/end 各有截图和同字节 gate JSON；
- 八个按 canonical 顺序的 GREEN provider postcondition；
- schema-v2 时，canonical seed 生成→加载连续性、每段 start/end checkpoint、pre/action/post revision chain、
  same-lineage binding 与 process-tree/driver/lock cleanup。

以下只生成 no-launch attempt manifest；它不会启动 CK3。所有路径必须换成真实、hash-bound 输入：

```powershell
& $Python "$Repo\tools\run_zhongguo_phase2_capture_attempt.py" `
  --attempt-dir $NewAttempt `
  --source-root $Repo `
  --source-git-commit $PinnedSourceCommit `
  --observer-artifact $CompletionObserver `
  --seed-contract $ReadySeedContract `
  --media-preflight-report $FreshMediaPreflight `
  --expected-media-preflight-sha256 $FreshMediaPreflightSha256 `
  --bridge-dll $BridgeDll `
  --bridge-injector $BridgeInjector `
  --source-checkpoint-registry $SourceCheckpointRegistry `
  --product-source $ProductSource `
  --product-projection $ProductProjectionName `
  --product-projection-manifest $ProductProjectionManifest `
  --frontend-first-load-save-name $SeedSaveName
```

只有该 manifest 为 GREEN 后，才可在 CK3 串行槽用完全相同参数加 `--execute`。失败 attempt 必须保留，不能覆盖重跑。

## 双语字幕与候选渲染

当前权威 authoring 合同是中文主旁白/主视觉文字、英文次视觉文字，画面同时带 `zh-CN` 与 `en` 两轨字幕；声音固定
`zh-CN-XiaoxiaoNeural`。编辑先按 `subtitle_zh_cn_lines` / `subtitle_en_lines` 的语义断句插入换行，renderer
只在每个编辑行内部按真实字体宽度再换行。媒体门要求：

- 1920×1080；字幕安全区 left/right `90`、top/bottom `64`；
- 中文 `Microsoft YaHei UI` 46 px、英文 `Segoe UI` 30 px，轨道分别保留自己的垂直边距；
- H.264/libx264、`yuv420p`、AAC 48 kHz stereo、MP4，时长 `<1200s`；
- 两个 cut 分别拥有项目配置、work/run/artifact/output、候选、审阅、signoff、export 与 publication receipt。

正式制作时才执行以下第一步；**本轮未执行**：

```powershell
git -C $Promo fetch origin main --prune
git -C $Promo merge --ff-only origin/main
if (git -C $Promo status --short) { throw 'promo tool checkout is dirty' }
$ToolHead = git -C $Promo rev-parse HEAD
if ($ToolHead -ne (git -C $Promo rev-parse origin/main)) {
  throw 'promo tool HEAD != origin/main'
}
$env:XAR_PROMO_SOURCE = $Promo
```

每个 cut 先对同一个 GREEN capture 分别做 footage intake、具名 1.0× source review、authoring promotion 与 fresh
media preflight，再运行：

```powershell
# $Cut = 'character-led' 或 'institution-led'
# $Project/$RunId/$Work 必须使用该 cut 自己的值和新目录。
& $Python "$Repo\mod_zhongguo_style\tools\prime_phase2_tts_cache.py" `
  --cut $Cut --project-config $Project `
  --media-preflight-report $MediaPreflight `
  --expected-media-preflight-sha256 $MediaSha256 `
  --tts-cache $TtsCache --output $TtsPrimeReceipt `
  --ffmpeg ffmpeg --ffprobe ffprobe

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut $Cut --project-config $Project --capture-root $Capture `
  --seed-preflight-report $SeedPreflight `
  --media-preflight-report $MediaPreflight `
  --expected-media-preflight-sha256 $MediaSha256 `
  --work-dir $Work --tts-cache $TtsCache `
  --ffmpeg ffmpeg --ffprobe ffprobe --run-id $RunId --validate-only

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut $Cut --project-config $Project --capture-root $Capture `
  --seed-preflight-report $SeedPreflight `
  --media-preflight-report $MediaPreflight `
  --expected-media-preflight-sha256 $MediaSha256 `
  --work-dir $Work --tts-cache $TtsCache `
  --ffmpeg ffmpeg --ffprobe ffprobe --run-id $RunId
```

固定映射：

- `character-led` / `phase2-character-led-candidate` →
  `deliverable/zhongguo-361-phase2-character-led.mp4`；
- `institution-led` / `phase2-institution-led-candidate` →
  `deliverable/zhongguo-361-phase2-institution-led.mp4`。

精确的 intake、promotion、media-preflight、materializer、audit、signoff 与 export 参数由
`tools/plan_zhongguo_phase2_final_promo.py` 为两个 cut 分别生成；权威长命令卡见
`phase2-dual-cut-production.md`。不得用 legacy single-cut ID 生产这两条正式片。

## 审阅、导出与发布回执门

每个 cut 必须独立完成以下门，另一条片的回执不能借用：

1. 具名审阅者以 1.0× 看完八段原始素材，签署 cut-specific source-review receipt；只有画面支持的 cue 才能 promote。
2. candidate build 后 materialize bound ffprobe、final storyboard、frame evidence bundle、pending review package 与
   release-export policy；自动 claims audit 只能报告结果，不能授予人工批准。
3. 两位不同的具名审阅者分别提交 `claims-and-source-pass` 与 `final-candidate-pass`：完整 1.0×、decision=approved、
   timestamp、candidate bytes/SHA 与 claims-audit SHA 全部一致。
4. `xar_promo.cli signoff` 必须把真实 reviewer/decision 写入该 cut 的 run manifest，并绑定精确 MP4 bytes/SHA。
5. `validate --profile release`、`export --validate-only`、`export` 通过；export manifest、run manifest、candidate 与
   exported MP4 hashes 必须一致，bundle 只包含 allowlist 文件。
6. 发布不是仓库工具动作。必须先有 owner-approved publish-target authority：明确 platform、target/account、HTTPS
   locator prefix、credential reference/availability、批准人和时间。上传后另存真实 publication receipt，证明
   `remote_verified=true`，HTTPS locator 位于获批 prefix 下，并绑定 authority、candidate、exported media 与 export
   manifest 的 bytes/SHA。
7. `zg361_phase2_final_promo_completion_attestation` 只有在 candidate/probe/run、claims audit、两份独立人审、
   approved signoff、export、target authority 和 publication receipt 全部同字节闭合后才可成为 `COMPLETE`。

当前以上所有媒体后置门都尚未开始；这是由 `0/8` footage 首门决定的诚实状态，不是可用静态测试提升的状态。

## 本轮静态审计

宣传侧 focused suite 首次发现一个真实的测试夹具漂移：Incident registry fixture 仍旧写成旧语义
`owner_character_id == player_character_id`，使“全部输入绑定后 capture plan 应 GREEN”的用例变 RED。fixture 已改为
当前 `ce458af` 权威语义的 distinct notice owner；没有修改生产 provider 或 runner。
