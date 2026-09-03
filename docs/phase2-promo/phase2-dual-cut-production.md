# 天朝二期双版本制作合同

状态：**两版均为 authoring draft / 非 live / 未生成媒体**。

用户要求保留并制作两种不同导演思路。本合同让它们共享同一组八段真实 CK3 原始证据，同时拥有各自独立的剪辑、旁白、运行目录、
候选交付物和最终审阅链。共享素材不等于共享叙事结论；任何跨人物、跨案件或跨周期关系仍须由画面明示，不得靠剪辑补出因果。

## 两个版本

| 剪辑 ID | 导演主角 | 项目配置 | 声明/旁白账本 | 默认运行 ID | 候选交付物 |
|---|---|---|---|---|---|
| `character-led` | 一名官员走过完整考核季 | `phase2-promo-character-project.json` | `phase2-authoring-character-claims.json` | `phase2-character-led-candidate` | `zhongguo-361-phase2-character-led-video` → `deliverable/zhongguo-361-phase2-character-led.mp4` |
| `institution-led` | 制造、批准并延续一个 C 的制度 | `phase2-promo-institution-project.json` | `phase2-authoring-institution-claims.json` | `phase2-institution-led-candidate` | `zhongguo-361-phase2-institution-led-video` → `deliverable/zhongguo-361-phase2-institution-led.mp4` |

两份权威导演处理稿分别为 `phase2-character-director-treatment.md` 与
`phase2-institution-director-treatment.md`；它们与本文件分工：处理稿决定戏剧结构，本文件决定两条可复现的制作与证据边界。

外部 `zhongguo_361_phase2` preset 的底层 `project.id` 仍必须是 `zhongguo-361-phase2-promo`。两版的项目级身份由不同配置路径、标题、
cue ID 前缀和配置文件 SHA 共同确定；剪辑级身份由上表的 cut/run/artifact/output 四组互不相同的 ID 确定。不得为了让底层 ID 看起来不同而
修改已发布 preset 或绕过其验证。

## 共享八段，独立成片

两版都严格消费以下 canonical spans，顺序和 provider postcondition 不变：

1. `phase2_fact_quota_calibration`
2. `phase2_receipt_appeal_pip`
3. `phase2_manager_governance`
4. `phase2_promotion_compensation`
5. `phase2_hc_workforce`
6. `phase2_projects_metrics`
7. `phase2_incidents_operations`
8. `phase2_cross_cycle_endgame`

允许共享的是已经通过 intake 的原始录像、timeline、evidence index、clean frames 和其字节哈希。两版必须分别完成以下内容：

- 根据各自处理稿做第一次 1× 素材审阅，并只提升画面真正支持的 cue；
- 使用各自配置 SHA 生成/绑定媒体环境 receipt；
- 使用不同 `work-dir` 与 `run-id`；
- 分别做 claims audit、最终 1× 审阅、signoff、export 和 publication receipt；
- 任一版本失败或被驳回，不得借用另一版本的审阅结果给自己开绿灯。

内容寻址的 Xiaoxiao TTS cache 可以共用，但两个版本不同的 cue 文本会自然得到不同缓存键。相同句子复用相同音频字节是缓存命中，不是
审阅复用。

## 当前 authoring 边界

两个 cut ledger 都是覆盖层：它们只替换旁白、双语字幕和开场/尾卡标题。八段 footage binding、required postcondition、可见观测清单、
evidence path 与 cannot-claim 规则全部从 `phase2-authoring-claims.json` 按 SHA-256 继承。validator 会先展开覆盖层再跑原有完整校验，
因此某个版本不能通过删掉 claim 字段来放宽证据要求。

当前两份项目仍保持全部章节 `planned`、`cues=[]`、`artifact_ids=[]`；两份 cut ledger 的所有 cue 仍为
`release_usable=false`。这表示剧本已经落盘，但真实镜头尚未到齐，不能称作 candidate、live、release-ready、exported 或 published。

## 无媒体校验

```powershell
py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py `
  --ledger mod_zhongguo_style/promo/phase2-authoring-character-claims.json `
  --validate-only

py mod_zhongguo_style/tools/validate_phase2_authoring_claims.py `
  --ledger mod_zhongguo_style/promo/phase2-authoring-institution-claims.json `
  --validate-only
```

两份 no-media runbook 使用同一个 `<GREEN_EIGHT_SPAN_CAPTURE>`，但必须指定不同的新目录：

```powershell
py tools/plan_zhongguo_phase2_final_promo.py `
  --project-config mod_zhongguo_style/promo/phase2-promo-character-project.json `
  --authoring-ledger mod_zhongguo_style/promo/phase2-authoring-character-claims.json `
  --capture-root <GREEN_EIGHT_SPAN_CAPTURE> `
  --tts-cache <SHARED_CONTENT_ADDRESSED_CACHE> `
  --work-dir <NEW_CHARACTER_WORK_DIR> `
  --output <NEW_CHARACTER_RUNBOOK_JSON>

py tools/plan_zhongguo_phase2_final_promo.py `
  --project-config mod_zhongguo_style/promo/phase2-promo-institution-project.json `
  --authoring-ledger mod_zhongguo_style/promo/phase2-authoring-institution-claims.json `
  --capture-root <GREEN_EIGHT_SPAN_CAPTURE> `
  --tts-cache <SHARED_CONTENT_ADDRESSED_CACHE> `
  --work-dir <NEW_INSTITUTION_WORK_DIR> `
  --output <NEW_INSTITUTION_RUNBOOK_JSON>
```

runbook 会把正确的 `--cut`、配置、默认 run ID、artifact ID 与输出路径写入后续命令。正式制作前仍须先 fresh fetch/fast-forward
宣传工具并证明 clean 且 `HEAD == origin/main`；本文和 validate-only 结果都不能替代该前置条件。

## 旧入口兼容

`phase2-promo-project.json`、`phase2-authoring-claims.json`、`phase2-candidate`、`zhongguo-361-phase2-video` 和
`deliverable/zhongguo-361-phase2.mp4` 暂时保留为 legacy single-cut 合同，供旧 receipt、测试和命令复核。新的双成片生产不得继续使用
legacy 名称，以免审阅者无法判断正在签哪一个版本。

## 8/8 素材到齐后的真实媒体命令链

下面两条链彼此独立；它们只共享已经通过 intake 的八段原始素材和内容寻址 TTS cache。`<...>` 必须替换为真实路径或刚刚打印出的真实哈希，不能使用占位内容执行。两条链都必须先让宣传工具完成 fresh fetch/fast-forward，并设置 `XAR_PROMO_SOURCE`，确保 Python 和后续 `xar-promo` 命令读取的是同一份最新源码。

### 人物线版本

```powershell
$Repo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$Promo = 'Z:\workspace\xar_promo_toolchain'
$Python = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$Capture = '<GREEN_EIGHT_SPAN_CAPTURE>'
$SeedPreflight = '<GREEN_SEED_PREFLIGHT_JSON>'
$TtsCache = '<SHARED_CONTENT_ADDRESSED_TTS_CACHE>'
$Work = '<NEW_CHARACTER_WORK_DIR>'
$Authoring = "$Work-authoring"
$env:XAR_PROMO_SOURCE = $Promo

git -C $Promo fetch origin
git -C $Promo merge --ff-only origin/main
if (git -C $Promo status --short) { throw 'promo tool checkout is dirty' }
$ToolHead = git -C $Promo rev-parse HEAD
if ($ToolHead -ne (git -C $Promo rev-parse origin/main)) { throw 'promo tool HEAD != origin/main' }

& $Python "$Repo\tools\zhongguo_phase2_footage_intake.py" `
  --capture-root $Capture --output "$Authoring\footage-intake.json"

# 这里暂停：具名审阅者按人物线 source checklist 以 1.0x 看完八段原片，
# 将真实签署的 zg361_phase2_source_review_receipt 写入下列路径。
$SourceReview = "$Authoring\source-review-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\promote_phase2_reviewed_authoring.py" `
  --project-config "$Repo\mod_zhongguo_style\promo\phase2-promo-character-project.json" `
  --authoring-ledger "$Repo\mod_zhongguo_style\promo\phase2-authoring-character-claims.json" `
  --footage-intake-report "$Authoring\footage-intake.json" `
  --source-review-receipt $SourceReview `
  --output-project "$Authoring\phase2-promo-character-project.json" `
  --output-receipt "$Authoring\authoring-promotion-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\preflight_phase2_media.py" `
  --output "$Authoring\media-preflight.json" `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --expected-toolchain-head $ToolHead --capture-root $Capture `
  --planned-work-dir $Work --planned-tts-cache $TtsCache
$MediaSha = (Get-FileHash -Algorithm SHA256 "$Authoring\media-preflight.json").Hash

& $Python "$Repo\mod_zhongguo_style\tools\prime_phase2_tts_cache.py" `
  --cut character-led `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha --tts-cache $TtsCache `
  --output "$Authoring\tts-cache-prime-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut character-led `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --capture-root $Capture --seed-preflight-report $SeedPreflight `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha `
  --work-dir $Work --tts-cache $TtsCache `
  --run-id phase2-character-led-candidate --validate-only

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut character-led `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --capture-root $Capture --seed-preflight-report $SeedPreflight `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha `
  --work-dir $Work --tts-cache $TtsCache `
  --run-id phase2-character-led-candidate
```

人物线候选固定落到 `$Work\deliverable\zhongguo-361-phase2-character-led.mp4`。

### 制度群像版本

```powershell
$Repo = 'Z:\ck3_mod_rewrite\_root-promo-split-20260902'
$Promo = 'Z:\workspace\xar_promo_toolchain'
$Python = 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe'
$Capture = '<GREEN_EIGHT_SPAN_CAPTURE>'
$SeedPreflight = '<GREEN_SEED_PREFLIGHT_JSON>'
$TtsCache = '<SHARED_CONTENT_ADDRESSED_TTS_CACHE>'
$Work = '<NEW_INSTITUTION_WORK_DIR>'
$Authoring = "$Work-authoring"
$env:XAR_PROMO_SOURCE = $Promo

git -C $Promo fetch origin
git -C $Promo merge --ff-only origin/main
if (git -C $Promo status --short) { throw 'promo tool checkout is dirty' }
$ToolHead = git -C $Promo rev-parse HEAD
if ($ToolHead -ne (git -C $Promo rev-parse origin/main)) { throw 'promo tool HEAD != origin/main' }

& $Python "$Repo\tools\zhongguo_phase2_footage_intake.py" `
  --capture-root $Capture --output "$Authoring\footage-intake.json"

# 这里暂停：另一份制度群像 source checklist 必须由具名审阅者真实看完并签署。
$SourceReview = "$Authoring\source-review-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\promote_phase2_reviewed_authoring.py" `
  --project-config "$Repo\mod_zhongguo_style\promo\phase2-promo-institution-project.json" `
  --authoring-ledger "$Repo\mod_zhongguo_style\promo\phase2-authoring-institution-claims.json" `
  --footage-intake-report "$Authoring\footage-intake.json" `
  --source-review-receipt $SourceReview `
  --output-project "$Authoring\phase2-promo-institution-project.json" `
  --output-receipt "$Authoring\authoring-promotion-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\preflight_phase2_media.py" `
  --output "$Authoring\media-preflight.json" `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --expected-toolchain-head $ToolHead --capture-root $Capture `
  --planned-work-dir $Work --planned-tts-cache $TtsCache
$MediaSha = (Get-FileHash -Algorithm SHA256 "$Authoring\media-preflight.json").Hash

& $Python "$Repo\mod_zhongguo_style\tools\prime_phase2_tts_cache.py" `
  --cut institution-led `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha --tts-cache $TtsCache `
  --output "$Authoring\tts-cache-prime-receipt.json"

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut institution-led `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --capture-root $Capture --seed-preflight-report $SeedPreflight `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha `
  --work-dir $Work --tts-cache $TtsCache `
  --run-id phase2-institution-led-candidate --validate-only

& $Python "$Repo\mod_zhongguo_style\tools\build_phase2_promo_video.py" `
  --cut institution-led `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --capture-root $Capture --seed-preflight-report $SeedPreflight `
  --media-preflight-report "$Authoring\media-preflight.json" `
  --expected-media-preflight-sha256 $MediaSha `
  --work-dir $Work --tts-cache $TtsCache `
  --run-id phase2-institution-led-candidate
```

制度群像候选固定落到 `$Work\deliverable\zhongguo-361-phase2-institution-led.mp4`。builder 在不改变八段 capture/evidence canonical 顺序的前提下，将前台顺序改为“事实/配额 → 经理 → 告身/PIP → 晋升 → HC → 项目 → 事故 → 跨周期”，并在项目场后回切告身/PIP、在跨周期场后回切经理案卷。每次回切都显式裁成 2 秒，只复用已验证 source span 的画面，不重复原旁白；builder 生成独立的 48 kHz 双声道静音 WAV，并以独立 segment / narration artifact 留下可审计边界。

## 候选生成后的项目级 materializer

两条 candidate build 成功后，分别运行下面对应的一组命令。materializer 从各自 run 内已经保全的候选字节出发，生成该 cut 独立的 bound ffprobe、最终剪辑顺序 storyboard、pending review package、frame-only evidence bundle 和 release export policy。正常模式会调用 ffprobe，并用 FFmpeg 抽取审片定位帧；它不会调用 TTS、重编码候选、写人审结论、签核、导出或发布。`--validate-only` 不调用 ffprobe/FFmpeg，也不创建目录。

人物线：

```powershell
$Run = "$Work\candidate-run\run-manifest.json"
$Post = "$Work\candidate-run\post-candidate"
$Export = "$Work-export"

& $Python "$Repo\mod_zhongguo_style\tools\materialize_phase2_post_candidate.py" `
  --cut character-led `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --run-manifest $Run --output-root $Post --export-directory $Export `
  --validate-only

& $Python "$Repo\mod_zhongguo_style\tools\materialize_phase2_post_candidate.py" `
  --cut character-led `
  --project-config "$Authoring\phase2-promo-character-project.json" `
  --run-manifest $Run --output-root $Post --export-directory $Export

& $Python -m xar_promo.cli audit $Run `
  --subject-artifact-id zhongguo-361-phase2-character-led-video `
  --evidence-bundle "$Post\evidence-bundle.json" `
  --report "$Post\automated-audit.json" `
  --report-artifact-id character-led-automated-audit
```

制度群像线：

```powershell
$Run = "$Work\candidate-run\run-manifest.json"
$Post = "$Work\candidate-run\post-candidate"
$Export = "$Work-export"

& $Python "$Repo\mod_zhongguo_style\tools\materialize_phase2_post_candidate.py" `
  --cut institution-led `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --run-manifest $Run --output-root $Post --export-directory $Export `
  --validate-only

& $Python "$Repo\mod_zhongguo_style\tools\materialize_phase2_post_candidate.py" `
  --cut institution-led `
  --project-config "$Authoring\phase2-promo-institution-project.json" `
  --run-manifest $Run --output-root $Post --export-directory $Export

& $Python -m xar_promo.cli audit $Run `
  --subject-artifact-id zhongguo-361-phase2-institution-led-video `
  --evidence-bundle "$Post\evidence-bundle.json" `
  --report "$Post\automated-audit.json" `
  --report-artifact-id institution-led-automated-audit
```

每个 `$Post` 都会留下以下确定路径：`bound-ffprobe.json`、`final-storyboard.json`、`evidence-plan.json`、`evidence-bundle.json`、`automated-audit.json`、`pending-review/review-package.json`、`pending-review/review-template.json`、`release-export-policy.json` 和 `materialization-receipt.json`。后两份真人回执必须另写到 `human-reviews/claims-and-source-pass.json` 与 `human-reviews/final-candidate-pass.json`，两位具名审阅者均须以 1.0x 看完精确候选；materializer 不创建这两个文件。

两份真人回执齐全后，由操作员向 `materialization-receipt.json` 内的 `commands.signoff.fixed_argv` 追加真实的 `--reviewer` 与 `--decision approved|rejected`，再执行。只有真实批准已进入 run manifest，才执行 receipt 内已经完全实例化的 `commands.export_validate_only` 和 `commands.export`。`commands.publish` 固定为 `null`；外部发布仍须另有明确的 publish-target authority，不能由 materializer 猜测或代签。

上述两段普通 build 只生成**未审候选片**。随后仍须按各自 `review/` 入口分别完成 bound ffprobe、claims audit、两轮真实 1.0x 人审、`xar-promo signoff` 与本地 export；任何一条的审核结果不能借给另一条。发布目标尚未得到明确授权时，可以交付本地候选和 export，但不得伪造 publication receipt 或把状态写成 `COMPLETE`。
